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
# pylint: disable=missing-docstring,too-many-branches
# pylint: disable=too-many-instance-attributes,too-many-statements

from __future__ import print_function
import os 
import sys
import json
from os.path import basename
from time import sleep, time
from logging import (
    getLogger, Formatter, StreamHandler,
    DEBUG, INFO, WARNING, ERROR, CRITICAL,
)
from signal import SIGINT, SIGTERM, signal, SIG_IGN
from subprocess import Popen, PIPE
from threading import Event as ThreadEvent
from multiprocessing import cpu_count
from multiprocessing import (
    BoundedSemaphore as ProcessBoundedSemaphore,
    Pool as ProcessPool
)
import multiprocessing.util as mp_util
from xml.etree import ElementTree as ET
from redis import Redis, ConnectionError

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.config.browsereport.decoding import decode_browse_report
# needs to be set before ingest_browse_report is importable (legacy eoxserver/django gimmicks...)
path = "/var/www/ngeo/ngeo_browse_server_instance"
if path not in sys.path:
    sys.path.append(path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ngeo_browse_server_instance.settings')
from ngeo_browse_server.control.ingest import ingest_browse_report


LOGGER_NAME = "browsewatchd"

# default daemon ID 
# Make sure each running instance has a unique-id or bad things happen.
DEF_DAEMON_ID = "default"

# Redis set containing the list of the watched collections
DEF_COLLECTION_LIST = "ingestion_queues"

# extra keys added to those found in the collection list
EXTRA_KYES = ["ingest_queue"]   # added for backward compatibility

MAX_WORKERS_PER_CPU = 16        # limit of allowed workers per CPU
DEF_N_WORKERS = 2               # default number of workers
DEF_REDIS_HOST = "localhost"    # default Redis hostname
DEF_REDIS_PORT = 6379           # default Redis port
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

ngeo_config = get_ngeo_config()
# some default configs
ngeo_config.set('control.ingest', "delete_on_success", True)
ngeo_config.set('control.ingest', "leave_original", False)


def parse_report_signature(report, logger):
    def _extract_text(xml, label, path):
        element = xml.find(path)
        if element is None:
            raise Exception("Failed to extract %s!" % label)
        return element.text
    try:
        xml = ET.fromstring(report)
        collection_id = _extract_text(xml, "collection identifier", XPATH_BR_BROWSE_TYPE)
        product_id = _extract_text(xml, "product identifier", XPATH_BR_BROWSE_IDENTIFIER)
    except Exception as error:
        logger.error("Failed to parse the browse report! (%s)", error)
        return None
    return collection_id, product_id


def handle_browse_report(job):
    """ Process browse report - ingest it to ngeo_browse_server """
    logger = getLogger(LOGGER_NAME)
    logger.info("Ingesting %s ...", job['job_id'])
    try:
        document = ET.fromstring(job["report"])
        parsed_browse_report = decode_browse_report(document)
    except Exception as error:
        logger.error("Failed to parse the browse report! (%s)", error)
        raise

    logger.info("Ingesting browse report with %d browse%s."
                   % (len(parsed_browse_report), 
                      "s" if len(parsed_browse_report) > 1 else ""))
    try:
        results = ingest_browse_report(parsed_browse_report, config=ngeo_config)
    except Exception as error:
        logger.error("Failed to ingest the file! (%s)", error)
        raise

    logger.info("%d browse%s handled, %d successfully replaced "
                "and %d successfully inserted."
                    % (results.to_be_replaced,
                       "s have been" if results.to_be_replaced > 1 
                       else " has been",
                       results.actually_replaced,
                       results.actually_inserted))


def wp_handle_browse_report(job):
    """ Process browse report. Executed by the worker process. """
    try:
        handle_browse_report(job)
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
        # pylint: disable=no-self-argument,protected-access,not-callable
        """ Decorator handling redis connection errors. """
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
        self._keys_last_update = float("-inf") # never
        #self._terminate = False
        self._terminated = ThreadEvent()
        self._redis_connection_trial = 0
        self._daemon_id = daemon_id
        self.buffer_key = "browsewatchd:browse_report_buffer:%s" % daemon_id
        self.jobs_key = "browsewatchd:ingestion_jobs:%s" % daemon_id

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
            self.worker_semaphore.release()
            self.logger.debug("Semaphore released.")
            error = job.get('error')
            if error:
                self.logger.error(
                    "Browse report ingestion failed! (%s: %s)",
                    type(error).__name__, error
                )
            self.logger.debug("Removing job %s ...", job["job_id"])
            try:
                self.remove_job(job["job_id"])
            except self.Terminated:
                self.logger.debug("Job %s removal terminated.", job["job_id"])
            else:
                self.logger.debug("Job %s removed.", job["job_id"])

        try:
            for job in self.read_jobs():
                self.worker_pool.apply_async(
                    wp_handle_browse_report, [job], {}, callback=callback
                )
        except self.Terminated:
            pass

        self.logger.debug("Exiting the main loop.")

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

    def read_jobs(self):
        """ Generator reading browse reports from the Redis keys.
        """
        slots_iterator = self.get_slots()

        # process the unfinished jobs
        unfinished_jobs = self.list_unfinished_jobs()
        if unfinished_jobs:
            self.logger.warning(
                "%d unfinished job(s) found!", len(unfinished_jobs)
            )
            for job_id in unfinished_jobs:
                slot = next(slots_iterator)
                job = self.get_unfinished_job(job_id)
                if job:
                    self.logger.info("Unfinished ingestion request loaded: %s", job["job_id"])
                    yield job
                else:
                    slot.release()
                    self.logger.debug("Semaphore released.")

        # process regular jobs
        for slot in slots_iterator:
            self.update_keys()
            job = self.get_new_job()
            if job:
                self.logger.info("New ingestion request received: %s", job["job_id"])
                yield job
            else:
                slot.release()
                self.logger.debug("Semaphore released.")
                if self._terminated.wait(self.REDIS_POLL_INTERVAL):
                    raise self.Terminated

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

        def _get_report(keys):
            pipeline = self.redis.pipeline()
            # read reports from the buffer if non-empty
            pipeline.lindex(self.buffer_key, -1)
            # get number of non-empty keys
            #pipeline.exists(*keys) # not supported by the RHEL6 redis-py
            #report, keys_count = pipeline.execute()
            for key in keys:
                pipeline.exists(key)
            response = pipeline.execute()
            report, keys_count = response[0], sum(response[1:])
            if report: # buffer is non-empty
                self.logger.debug("Reading buffered report.")
                return report # item from the buffer is returned
            if keys_count: # there are reports to be read
                # filling buffer from the watched pipelines
                pipeline = self.redis.pipeline()
                for key in keys:
                    pipeline.rpoplpush(key, self.buffer_key)
                result = pipeline.execute()
                # return the first report
                for key, report in zip(keys, result):
                    if report:
                        self.logger.debug("Buffering report from %s.", key)
                for report in result:
                    if report:
                        self.logger.debug("Reading first popped report.")
                        return report
                self.logger.debug("No report available.")
            return None # no report available

        def _create_new_job(report):
            if report is None:
                return None
            pipeline = self.redis.pipeline()
            result = parse_report_signature(report, self.logger)
            if result:
                collection_id, product_id = result
                job_id = "%s/%s" % (collection_id, product_id)
                self.logger.debug("Creating job %s ..." % job_id)
                # save new job
                job = dict(
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

        return _create_new_job(_get_report(self.keys))

    @_redis_call
    def update_keys(self):
        """ Update the list of the watched ingestion queues (Redis keys). """
        if (time() - self._keys_last_update) < self.REDIS_KEY_SET_REFRESH:
            return

        result = self.redis.smembers(self.key_set) or set()

        self._keys_last_update = time()

        new_keys = result | set(EXTRA_KYES)
        old_keys = set(self.keys)

        self.keys = list(new_keys)

        for key in old_keys - new_keys:
            self.logger.info("Ingestion queue %s removed.", key)
        for key in new_keys - old_keys:
            self.logger.info("Ingestion queue %s added.", key)

        if old_keys != new_keys:
            self.logger.info(
                "Consumed ingestion queues: %s",
                " ".join(self.keys)
            )


def init_worker():
    """ Process pool initialization. """
    # prevent SIGINT propagation to the subprocesses
    signal(SIGINT, SIG_IGN)


def start_browsewatchd(redis_host, redis_port, redis_key_set, n_workers, daemon_id):
    BrowseWatchDaemon(
        redis=Redis(host=redis_host, port=redis_port),
        key_set=redis_key_set,
        logger=getLogger(LOGGER_NAME),
        worker_pool=ProcessPool(
            n_workers,
            init_worker,
            #maxtasksperchild=max_tasks_per_worker, # does not work in Python 2.6
        ),
        daemon_id=daemon_id,
        worker_semaphore=ProcessBoundedSemaphore(n_workers),
    ).run()


def main(*args):
    try:
        kwargs = parse_args(*args)
        set_stream_handler(getLogger(), kwargs.pop('log_level'))
        set_stream_handler(mp_util.get_logger(), mp_util.SUBWARNING)
        start_browsewatchd(**kwargs)
    except CommandError as error:
        print_error(str(error))
        return 1
    return 0


def set_stream_handler(logger, level=DEBUG):
    """ Set stream handler to the logger. """
    formatter = Formatter('%(levelname)s: %(module)s: %(message)s')
    handler = StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(min(level, logger.level))


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
    #max_tasks_per_worker = DEF_MAX_TASKS_PER_WORKER

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
            #elif option == "--max-tasks-per-worker":
            #    max_tasks_per_worker = int(next(it_args))
            #    if not max_tasks_per_worker:
            #        max_tasks_per_worker = None
            #    if max_tasks_per_worker < 0:
            #        raise ValueError(
            #            "Invalid max. tasks-per-worker count "
            #            "%s!" % max_tasks_per_worker
            #        )
            elif option in ("-v", "--verbosity"):
                try:
                    log_level = LOG_LEVEL[next(it_args)]
                except KeyError as key:
                    raise ValueError("Invalid verbosity %s !" % key)
            elif option in ("-h", "--help"):
                print_usage(args[0])
                sys.exit(0)
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
        #max_tasks_per_worker=max_tasks_per_worker,
        log_level=log_level,
    )


def unique(keys):
    """ Filter out repeating keys. """
    existing = set()
    for key in keys:
        if not key in existing:
            existing.add(key)
            yield key


def print_usage(execname):
    """ print command usage """
    print(
        "USAGE: %s [--host <redis-host>][--port <redis-port>]"
        "[--nworkers <n-processes>]"
        "[-id <daemon-id>]"
        #"[--max-tasks-per-worker <max-tasks-per-worker>]"
        "[--verbosity *INFO|DEBUG|WARNING|ERROR|CRITICAL] "
        "[<redis-collection-list>] " % basename(execname),
        file=sys.stderr
    )


def print_error(message):
    """ print error message """
    print("ERROR: %s" % message, file=sys.stderr)


class CommandError(Exception):
    """ Command error exception. """


if __name__ == "__main__":
    sys.exit(main(*sys.argv))