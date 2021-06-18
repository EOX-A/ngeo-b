#-------------------------------------------------------------------------------
#
#  Browse reports' feed watch daemon
#
# Authors: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
# pylint: disable=missing-docstring,too-many-branches,line-too-long
# pylint: disable=too-many-instance-attributes,too-many-statements
# pylint: disable=too-few-public-methods

from __future__ import print_function
import sys
import json
from os import environ
from os.path import basename
from datetime import datetime
from time import sleep, time
from logging import (
    getLogger, LoggerAdapter, Filter, Formatter, StreamHandler,
    DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET,
)
from signal import SIGINT, SIGTERM, signal, SIG_IGN
from threading import Event as ThreadEvent
from multiprocessing import cpu_count
from multiprocessing import (
    BoundedSemaphore as ProcessBoundedSemaphore,
    Pool as ProcessPool
)
import multiprocessing.util as mp_util
from redis import Redis, ConnectionError
from lxml import etree

LOGGER_NAME = "browsewatchd"

# default daemon ID
# Make sure each running instance has a unique-id or bad things happen.
DEF_DAEMON_ID = "browsewatchd-cli"

# Redis set containing the list of the watched collections
DEF_COLLECTION_LIST = "ingestion_queues"

# extra keys added to those found in the collection list
EXTRA_KYES = ["ingest_queue"]   # added for backward compatibility

# max number of simultaneously processed reports from a singe queue
# assuming collection == ingestion queue == seeded tile-set
# larger values increase chances of seeding lock time-outs
MAX_JOBS_PER_INGESTION_QUEUE = 2

MAX_WORKERS_PER_CPU = 16        # limit of allowed workers per CPU
DEF_N_WORKERS = 2               # default number of workers
DEF_REDIS_HOST = "localhost"    # default Redis hostname
DEF_REDIS_PORT = 6379           # default Redis port
DEF_BS_INSTANCE_PATH = environ.get(  # browse server instance path
    "INSTANCE_PATH", "/var/www/ngeo/ngeo_browse_server_instance"
)
DEF_BS_SETTINGS_MODULE = environ.get( # browse server instance settings module
    "DJANGO_SETTINGS_MODULE", "ngeo_browse_server_instance.settings"
)
#DEF_MAX_TASKS_PER_WORKER = 16   # worker restarted after this number of tasks

# Browse Report XML paths
XPATH_BR_BROWSE_TYPE = (
    "{http://ngeo.eo.esa.int/schema/browseReport}browseType"
)
XPATH_BR_BROWSE_IDENTIFIER = (
    "{http://ngeo.eo.esa.int/schema/browseReport}browse/"
    "{http://ngeo.eo.esa.int/schema/browseReport}browseIdentifier"
)

LOG_LEVEL = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "ERROR": ERROR,
    "CRITICAL": CRITICAL,
}

# non-propagated loggers which require explicit setup
DEF_EXTRA_LOGGING = False
EXTRA_HANDLED_LOGGERS = [
    'eoxserver',
    'ngeo_browse_server',
    'ngEO-ingest',
]


class CommandError(Exception):
    """ Command error exception. """


def parse_report_signature(report, logger):
    def _extract_text(xml, label, path):
        element = xml.find(path)
        if element is None:
            raise Exception("Failed to extract %s!" % label)
        return element.text
    try:
        xml = etree.fromstring(report.encode('utf-8'))
        collection_id = _extract_text(xml, "collection identifier", XPATH_BR_BROWSE_TYPE)
        product_id = _extract_text(xml, "product identifier", XPATH_BR_BROWSE_IDENTIFIER)
    except Exception as error:
        logger.error("Failed to parse the browse report! (%s)", error)
        return None
    return collection_id, product_id


def handle_browse_report_inline(job_id, report, **kwargs):
    """ Process browse report in a subprocess. """
    JobIdLoggingContextFilter.JOB_ID = job_id
    logger = getLogger(LOGGER_NAME)
    logger.info("Starting ingestion ...")
    try:
        ingest_browse_report(
            decode_browse_report(
                etree.fromstring(report.encode('utf-8'))
            )
        )
    except Exception as error:
        logger.error("Ingestion failed!", exc_info=True)
        raise
    logger.info("Ingested.")


def wp_handle_ingestion_job(job):
    """ Process browse report. Executed by the worker process. """
    job["started"] = time()
    try:
        handle_browse_report_inline(**job)
    except Exception as error:
        job.update(dict(stopped=time(), status="ERROR", error=error))
    else:
        job.update(dict(stopped=time(), status="OK"))
    return job


class BrowseWatchDaemon(object):
    WORKER_SEMAPHORE_TIMEOUT = 1 # second
    WORKER_TERMINATION_DELAY = 2 # seconds
    REDIS_KEY_SET_REFRESH = 15 # seconds
    REDIS_POLL_INTERVAL = 1 # second
    REDIS_CONNECTION_TIMEOUTS = [15, 30, 60, 120, 240] # seconds
    REDIS_STATUS_EXPIRE = 60 # second

    class KeyCounters(object):
        """ Key counters. Used to prioritize faster ingestion queues. """

        def __init__(self):
            self.counters = {}

        def __getitem__(self, key):
            return self.counters.get(key, 0)

        def __setitem__(self, key, value):
            self.counters[key] = value

        def __delitem__(self, key):
            self.counters.pop(key, None)

        def increment(self, key):
            """ Increment key counter. """
            self[key] = self[key] + 1

        def decrement(self, key):
            """ Decrement key counter. """
            count = self[key] - 1
            if count > 0:
                self[key] = count
            else:
                del self[key]

        def sort_keys(self, keys, max_count=1):
            """ Get keys sorted by the counter values.
            Only keys with not more than max_count are allowed.
            """
            return [
                key for _, _, key in sorted(
                    (self[k], i, k) for i, k in enumerate(keys)
                    if self[k] <= max_count
                )
            ]

    class Terminated(Exception):
        pass

    @property
    def connection_timeout(self):
        """ Get connection timeout in case of a failing redis connection. """
        return self.REDIS_CONNECTION_TIMEOUTS[min(
            self._redis_connection_trial,
            len(self.REDIS_CONNECTION_TIMEOUTS) - 1,
        )]

    def _redis_call(method):
        """ Decorator handling redis connection errors. """
        # pylint: disable=no-self-argument,protected-access,not-callable
        def _redis_call_wrapper(self, *args, **kwargs):
            self._redis_connection_trial = 0
            while True:
                try:
                    result = method(self, *args, **kwargs)
                except ConnectionError as error:
                    if self._terminated.is_set():
                        raise self.Terminated
                    self.logger.error(
                        "Cannot connect to the Redis server! (%s)", error
                    )
                    self._redis_connection_trial += 1
                    timeout = self.connection_timeout
                    self.logger.info(
                        "Redis connection re-try #%s in %ss",
                        self._redis_connection_trial, timeout
                    )
                    if self._terminated.wait(timeout):
                        raise self.Terminated
                else:
                    self._redis_connection_trial = 0
                    return result
        return _redis_call_wrapper

    def __init__(self, redis, key_set, worker_pool, worker_semaphore,
                 daemon_id, logger):
        self.worker_semaphore = worker_semaphore
        self.worker_pool = worker_pool
        self.logger = logger
        self.redis = redis
        self.key_set = key_set
        self.keys = []
        self._key_counter = self.KeyCounters()
        self._keys_last_update = float("-inf") # never
        self._terminated = ThreadEvent() # implements abortable sleep
        self._redis_connection_trial = 0
        self._daemon_id = daemon_id
        self.buffer_key = "browsewatchd:browse_report_buffer:%s" % daemon_id
        self.jobs_key = "browsewatchd:ingestion_jobs:%s" % daemon_id
        self.status_key = "browsewatchd:daemon_status:%s" % daemon_id

    def terminate(self, signum=None, frame=None):
        self.logger.info("Termination signal received ...")
        self.shutdown()

    def shutdown(self):
        """ Shutdown the daemon as clean-up the resources. """
        if self._terminated.is_set():
            return

        self.logger.info("Shutting down daemon ...")
        self._terminated.set()

        self.logger.debug("Disconnecting Redis connections ...")
        for connection in self.redis.connection_pool.get_all_connections():
            connection.disconnect()

        self.logger.debug("Closing worker pool ...")
        self.worker_pool.close()
        sleep(self.WORKER_TERMINATION_DELAY)

        self.logger.debug("Terminating subprocesses ...")
        self.worker_pool.terminate()

        self.logger.debug("Joining subprocesses ...")
        self.worker_pool.join()

        # update the daemon status
        try:
            self.redis.set(self.status_key, "STOPPED")
        except ConnectionError:
            raise

        self.redis = None
        self.worker_pool = None
        self.worker_semaphore = None

    def run(self):
        """ Run the daemon. """
        self.logger.info("Starting daemon ...")
        try:
            # set signal handlers
            signal(SIGINT, self.terminate)
            signal(SIGTERM, self.terminate)
            self.process_reports()
        finally:
            self.shutdown()
            self.logger.info("Daemon is halted.")

    def process_reports(self):
        """ Process ingested reports. """

        def callback(job):
            """ Worker callback. """
            job_logger = JobIdLoggingContextAdapter(self.logger, job["job_id"])
            self._key_counter.decrement(job.get('source'))
            self.worker_semaphore.release()
            self.logger.debug("Semaphore released.")
            error = job.get('error')
            if error:
                job_logger.error(
                    "Browse report ingestion failed! (%s)",
                    "%s: %s" % (type(error).__name__, error)
                    if str(error) else type(error).__name__
                )
                job_logger.info("Failed in %.1fs", job["stopped"] - job["started"])
            else:
                job_logger.info("Completed in %.1fs", job["stopped"] - job["started"])
                job_logger.debug("Removing job ...")
            try:
                self.remove_job(job["job_id"])
            except self.Terminated:
                job_logger.debug("Job removal terminated.")
            else:
                job_logger.debug("Job removed.")

        try:
            self._init_status()
            for job in self.read_jobs():
                self._key_counter.increment(job['source'])
                self.worker_pool.apply_async(
                    wp_handle_ingestion_job, [job], {}, callback=callback
                )
        except self.Terminated:
            pass

        self.logger.debug("Exiting the main loop.")

    def read_jobs(self):
        """ Generator reading ingestion jobs (browse reports) from the Redis keys.
        """
        slots_iterator = self.get_slots()

        # process unfinished jobs
        unfinished_jobs = self.list_unfinished_jobs()
        if unfinished_jobs:
            self.logger.warning(
                "%d unfinished job(s) found!", len(unfinished_jobs)
            )
            for job_id in unfinished_jobs:
                slot = next(slots_iterator)
                job = self.get_unfinished_job(job_id)
                if job:
                    JobIdLoggingContextAdapter(self.logger, job["job_id"]).info(
                        "Unfinished ingestion request loaded."
                    )
                    yield job
                else:
                    slot.release()
                    self.logger.debug("Semaphore released.")

        # process regular jobs
        for slot in slots_iterator:
            self.update_keys()
            job = self.get_new_job()
            if job:
                JobIdLoggingContextAdapter(self.logger, job["job_id"]).info(
                    "Unfinished ingestion request loaded."
                )
                yield job
            else:
                slot.release()
                self.logger.debug("Semaphore released.")
                if self._terminated.wait(self.REDIS_POLL_INTERVAL):
                    raise self.Terminated

    def get_slots(self):
        """ Generator wrapping the worker pool semaphore, yielding semaphore
        slot to proceed with the next report.
        """
        while not self._terminated.is_set():
            if self.worker_semaphore.acquire(True, self.WORKER_SEMAPHORE_TIMEOUT):
                if not self._terminated.is_set():
                    self.logger.debug("Semaphore acquired.")
                    yield self.worker_semaphore
            else:
                self.logger.debug("Semaphore timeout.")
        self.logger.debug("Exiting the semaphore loop.")
        raise self.Terminated

    @_redis_call
    def _init_status(self):
        """ Initialize deamon status. """
        pipeline = self.redis.pipeline()
        pipeline.get(self.status_key)
        pipeline.set(self.status_key, "RUNNING")
        status, _ = pipeline.execute()
        if status == "RUNNING":
            raise CommandError(
                "Another %s demon process is running! Stop the other "
                "process or use a different daemon id." % self._daemon_id
            )

    @_redis_call
    def list_unfinished_jobs(self):
        """ Get list of unfinished ingestion jobs. """
        return self.redis.hkeys(self.jobs_key)

    @_redis_call
    def get_unfinished_job(self, job_id):
        """ Get list of unfinished ingestion jobs. """
        job = self.redis.hget(self.jobs_key, job_id)
        return json.loads(job) if job else None

    @_redis_call
    def remove_job(self, job_id):
        self.redis.hdel(self.jobs_key, job_id)

    @_redis_call
    def get_new_job(self):
        """ Get new job. """

        def _move_key_to_tail(keys, key):
            try:
                index = keys.index(key)
            except ValueError:
                return keys # key not found - do nothing
            return keys[:index] + keys[index+1:] + keys[index:index+1]

        def _get_report():
            pipeline = self.redis.pipeline()
            # report daemon status
            pipeline.set(self.status_key, "RUNNING")
            pipeline.expire(self.status_key, self.REDIS_STATUS_EXPIRE)
            # read reports from the buffer if non-empty
            pipeline.lindex(self.buffer_key, -1)
            # check non-empty keys
            for key in self.keys:
                pipeline.exists(key)
            response = pipeline.execute()
            report = response[2]
            if report: # buffer is non-empty
                self.logger.debug("Reading buffered report.")
                return self.buffer_key, report # item from the buffer is returned
            # pick the non-empty keys and prioritize them by the key counter
            # prioritize keys with lower key counters
            # queues with reached MAX_JOBS_PER_INGESTION_QUEUE are skipped
            readable_keys = self._key_counter.sort_keys([
                key for key, count in zip(self.keys, response[3:]) if count > 0
            ], max_count=(MAX_JOBS_PER_INGESTION_QUEUE - 1))
            for key in readable_keys:
                report = self.redis.rpoplpush(key, self.buffer_key)
                if report:
                    self.logger.debug("Reading report from %s." % key)
                    # re-order keys to prevent reading from the same key
                    self.keys = _move_key_to_tail(self.keys, key)
                    return key, report

            self.logger.debug("No report available.")
            return None

        def _create_new_job(key, report):
            pipeline = self.redis.pipeline()
            result = parse_report_signature(report, self.logger)
            if result:
                collection_id, product_id = result
                job_id = "%s/%s" % (collection_id, product_id)
                JobIdLoggingContextAdapter(self.logger, job_id).debug(
                    "Creating job ..."
                )
                # save new job
                job = dict(
                    source=key,
                    job_id=job_id,
                    collection_id=collection_id,
                    product_id=product_id,
                    created=time(),
                    report=report,
                )
                pipeline.hset(self.jobs_key, job_id, json.dumps(job))
            else:
                job = None # ignore invalid reports
            # remove report from the buffer
            pipeline.lrem(self.buffer_key, report)
            pipeline.execute()
            return job

        # read report from the first available key
        result = _get_report()
        if result is None:
            return None
        return _create_new_job(*result)

    @_redis_call
    def update_keys(self):
        """ Update the list of the watched ingestion queues (Redis keys). """
        if (time() - self._keys_last_update) < self.REDIS_KEY_SET_REFRESH:
            return

        # get non-empty ingestion queues, empty queues are removed
        result = set(self.redis.execute_command('EVAL', (
            "for i,key in ipairs(redis.call('SMEMBERS',KEYS[1])) do "
            "if redis.call('EXISTS',key)==0 then "
            "redis.call('SREM', KEYS[1],key) "
            "end "
            "end;"
            "return redis.call('SMEMBERS',KEYS[1])"
        ), 1, self.key_set))

        self._keys_last_update = time()

        new_keys = result | set(EXTRA_KYES)
        old_keys = set(self.keys)

        if old_keys != new_keys:
            added_keys = new_keys - old_keys
            removed_keys = old_keys - new_keys

            # make sure the key order is preserved
            self.keys = list(added_keys) + [
                key for key in self.keys if key not in removed_keys
            ]

            for key in removed_keys:
                self.logger.info("Ingestion queue %s removed.", key)
            for key in added_keys:
                self.logger.info("Ingestion queue %s added.", key)

            self.logger.info(
                "Consumed ingestion queues: %s",
                " ".join(self.keys)
            )


def start_browsewatchd(redis_host, redis_port, redis_key_set, n_workers,
                       daemon_id, **kwargs):
    BrowseWatchDaemon(
        redis=Redis(host=redis_host, port=redis_port),
        key_set=redis_key_set,
        logger=getLogger(LOGGER_NAME),
        worker_pool=ProcessPool(n_workers, init_worker),
        daemon_id=daemon_id,
        worker_semaphore=ProcessBoundedSemaphore(n_workers),
    ).run()


def init_worker():
    """ Process pool initialization. """
    # prevent SIGINT propagation to the subprocesses
    signal(SIGINT, SIG_IGN)


def main(*args):
    try:
        kwargs = parse_args(*args)

        # setup django environment
        environ["DJANGO_SETTINGS_MODULE"] = kwargs.pop('django_settings_module')
        path = kwargs.pop('django_instance_path')
        if path not in sys.path:
            sys.path.append(path)

        # Django imports performed after the instance part configuration
        import_from_module("ngeo_browse_server.config.browsereport.decoding", "decode_browse_report")
        import_from_module("ngeo_browse_server.control.ingest", "ingest_browse_report")

        # setup console logging - must be performed AFTER the Django imports
        setup_logging(
            kwargs.pop('log_level'),
            [None] + EXTRA_HANDLED_LOGGERS if kwargs.pop('extra_logging')
            else [LOGGER_NAME]
        )

        # start the daemon
        start_browsewatchd(**kwargs)

    except CommandError as error:
        print_error(str(error))
        return 1
    return 0


def import_from_module(module_name, *object_names):
    """ Import objects from a module into the global scope.  This function
    emulates the global 'from <module> import <object>, ...' command.
    """
    module = __import__(module_name, fromlist=object_names)
    globals().update((name, getattr(module, name)) for name in object_names)


def setup_logging(log_level, loggers,):
    """ Setup logging. """
    for name in loggers or []:
        set_stream_handler(getLogger(name), log_level)
    set_stream_handler(mp_util.get_logger(), mp_util.SUBWARNING)


def set_stream_handler(logger, level=DEBUG):
    """ Set stream handler to the logger. """
    formatter = FormatterUTC('%(asctime)s %(job_id)s %(levelname)s %(name)s: %(message)s')
    handler = StreamHandler()
    handler.setLevel(level)
    handler.addFilter(JobIdLoggingContextFilter())
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(
        level if logger.level == NOTSET else min(level, logger.level)
    )


class FormatterUTC(Formatter):
    "Custom log formatter class."
    converter = datetime.utcfromtimestamp

    def formatTime(self, record, datefmt=None):
        """ Return the creation time of the specified LogRecord as formatted
        text.

        Note that this method uses the `datetime.datetime.strftime()` method
        rather then the `time.strftime` used by the `logging.Formatter` which
        if not able to format times with sub-second precision.
        """
        dts = self.converter(record.created)
        return dts.strftime(datefmt) if datefmt else dts.isoformat("T")+"Z"

    #def format(self, record):
    #    """ Format the specified record as text.
    #    This custom formatter escapes Unicode character and special characters
    #    such as new lines.
    #    """
    #    record.msg = record.msg.encode('unicode_escape').decode('utf-8')
    #    return Formatter.format(self, record)


class JobIdLoggingContextFilter(Filter):
    JOB_ID = None
    def filter(self, record):
        job_id = JobIdLoggingContextFilter.JOB_ID
        record.job_id = job_id if job_id is not None else (
            getattr(record, "job_id", "-")
        )
        return True


class JobIdLoggingContextAdapter(LoggerAdapter):
    def __init__(self, logger, job_id):
        LoggerAdapter.__init__(self, logger, {"job_id": job_id})


def parse_args(*args):
    """ Parse CLI argument. """
    # collection list is a Redis set containing the current list of browse
    # report ingestion queues
    daemon_id = DEF_DAEMON_ID
    collection_list = None
    n_workers = DEF_N_WORKERS
    redis_host = DEF_REDIS_HOST
    redis_port = DEF_REDIS_PORT
    log_level = INFO
    django_settings_module = DEF_BS_SETTINGS_MODULE
    django_instance_path = DEF_BS_INSTANCE_PATH
    extra_logging = DEF_EXTRA_LOGGING

    it_args = iter(args[1:])
    for option in it_args:
        try:
            if option == "--host":
                redis_host = next(it_args)
                if not redis_host:
                    raise ValueError("Invalid redis hostname!")
            elif option == "--port":
                redis_port = int(next(it_args))
                if redis_port < 1 or redis_port > 65535:
                    raise ValueError("Invalid redis port %s!" % redis_port)
            elif option in ("-n", "--nworkers"):
                n_workers = int(next(it_args))
                if n_workers < 1:
                    raise ValueError("Invalid worker count %s!" % n_workers)
            elif option in ("-i", "--id", "--daemon-id"):
                daemon_id = next(it_args)
                if not daemon_id:
                    raise ValueError("Invalid daemon id!")
            elif option == "--settings-module":
                django_settings_module = next(it_args)
                if not django_settings_module:
                    raise ValueError("Invalid django settings module!")
            elif option == "--instance-path":
                django_instance_path = next(it_args)
                if not django_instance_path:
                    raise ValueError("Invalid django instance path!")
            elif option in ("-v", "--verbosity"):
                try:
                    log_level = LOG_LEVEL[next(it_args)]
                except KeyError as key:
                    raise ValueError("Invalid verbosity %s !" % key)
            elif option in ("-h", "--help"):
                print_usage(args[0])
                sys.exit(0)
            elif option == "--extra-logging":
                extra_logging = True
            elif option == "--basic-logging":
                extra_logging = False
            elif option == "--":
                break # all following arguments are interpreted as keys
            elif option.startswith("-"):
                raise CommandError("Invalid input argument '%s'!" % option)
            else:
                if collection_list:
                    raise CommandError("Only one collection-list allowed!")
                collection_list = option
        except StopIteration:
            raise CommandError("Not enough input arguments!")
        except ValueError as error:
            raise CommandError(str(error))

    for item in it_args:
        if collection_list:
            raise CommandError("Only one collection-list allowed!")
        collection_list = item

    if not collection_list:
        collection_list = DEF_COLLECTION_LIST

    n_workers = min(MAX_WORKERS_PER_CPU * cpu_count(), n_workers)

    return dict(
        redis_host=redis_host,
        redis_port=redis_port,
        redis_key_set=collection_list,
        n_workers=n_workers,
        daemon_id=daemon_id,
        log_level=log_level,
        django_settings_module=django_settings_module,
        django_instance_path=django_instance_path,
        extra_logging=extra_logging,
    )


def print_usage(execname):
    """ print command usage """
    print(
        "USAGE: %s [options] [<redis-collection-list>] " % basename(execname),
        file=sys.stderr
    )
    print("\n".join([
        "ARGUMENTS:",
        "    <redis-collection-list>       [%s]" % DEF_COLLECTION_LIST,
        "        Optional Redis set key holding the list of the ingestion queues.",
        "OPTIONS:",
        "    --help | -h",
        "        Print command help.",
        "    --host <redis-host>           [%s]" % DEF_REDIS_HOST,
        "        Redis hostname",
        "    --port <redis-port>           [%s]" % DEF_REDIS_PORT,
        "        Redis port number",
        "    --nworkers | -n <no-workers>  [%s]" % DEF_N_WORKERS,
        "        Number or parallel processes. ",
        "    --id | -i <identifier>        [%s]" % DEF_DAEMON_ID,
        "        Daemon identifier, unique per each running daemon instance.",
        "    --settings-module <settings>  [%s]" % DEF_BS_SETTINGS_MODULE,
        "        Browse Server Django setting module.",
        "    --instance-path <path>        [%s]" % DEF_BS_INSTANCE_PATH,
        "        Browse Server Django instance path.",
        "   --verbosity | -v DEBUG|INFO|WARNING|ERROR|CRITICAL [INFO]",
        "        Logging verbosity.",
        "   --extra-logging",
        "        Output browse ingestion logging messages. By default, only",
        "        the daemon's log messages are printed.",
        "   --basic-logging",
        "        Print only the daemon's log messages.",
    ]), file=sys.stderr)


def print_error(message):
    """ print error message """
    print("ERROR: %s" % message, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
