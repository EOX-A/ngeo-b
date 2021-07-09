#-------------------------------------------------------------------------------
#
#  Browse reports' feed CLI monitor.
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
import re
import sys
import json
import os
import curses
from math import ceil
from datetime import datetime, timedelta
from os.path import basename, splitext
from time import time, sleep
from redis import Redis, ConnectionError

inf = float("inf")
nan = float("nan")


class CommandError(Exception):
    """ Command error exception. """


# special keys used by the browsewatchd daemon
BROWSEWATCHD_KEY_PREFIX = "browsewatchd:"
BUFFER_KEY_PREFIX = BROWSEWATCHD_KEY_PREFIX + "browse_report_buffer:"
JOBS_KEY_PREFIX = BROWSEWATCHD_KEY_PREFIX + "ingestion_jobs:"
STATUS_KEY_PREFIX = BROWSEWATCHD_KEY_PREFIX + "daemon_status:"
RE_DAEMON_KEY_PATTERN = re.compile(
    "^" + BROWSEWATCHD_KEY_PREFIX +
    r"(browse_report_buffer|ingestion_jobs|daemon_status):(?P<daemon_id>.*)"
)

# Redis set containing the list of the watched collections
DEF_COLLECTION_LIST = "ingestion_queues"

# extra keys added to those found in the collection list
EXTRA_KYES = ["ingest_queue"]   # added for backward compatibility
DEF_REDIS_HOST = "localhost"    # default Redis hostname
DEF_REDIS_PORT = 6379           # default Redis port

DEF_LOGFILE = splitext(basename(sys.argv[0]))[0] + ".log"


class CScreen(object):
    """ Curses screen object. """

    def __init__(self):
        self.screen = curses.initscr()
        self.column = 0
        self.line = 0
        self.tabs = []

    def __del__(self):
        curses.endwin()

    def move(self, line, column):
        self.column = column
        self.line = line

    def clear(self):
        self.move(0, 0)
        self.screen.clear()

    def refresh(self):
        self.screen.refresh()

    def write_line(self, line):
        line = str(line).split("\t", len(self.tabs)) # split tabs 
        it_tabs = iter(self.tabs) # iterate tab sizes
        column = self.column
        for part in line:
            self.screen.addstr(self.line, column, part)
            try:
                column += next(it_tabs)
            except StopIteration:
                break
        self.line += 1


class QueueState(object):
    MAX_HISTORY = 100

    def __init__(self, name, counter=0):
        self.name = name
        self.last_update = -inf
        self.counter = -1
        self.update(counter)
        self._reset_next = True

    def update(self, counter):
        item = (time(), counter)
        if counter > self.counter or self._reset_next:
            self.history = [item]
            self._reset_next = False
        elif counter < self.counter:
            self.history.append(item)

        self.history = self.history[-self.MAX_HISTORY:]
        self.last_update, self.counter = item

    @property
    def count(self):
        return self.counter

    @property
    def rate(self):
        """ Processing rate, seconds per image. """
        dtime, dcount = self.window_time, self.window_change
        return nan if dcount == 0 else dtime / dcount

    @property
    def completion_estimate(self):
        """ Estimate completion time. """
        return self.history[-1][0] + self.count * self.rate

    @property
    def window_change(self):
        """ observed window change """
        return self.history[0][1] - self.history[-1][1]

    @property
    def window_time(self):
        """ observed window time interval. """
        return self.history[-1][0] - self.history[0][0]

    @property
    def window_size(self):
        """ observed window time interval. """
        return len(self.history) / float(self.MAX_HISTORY)

    @property
    def changed(self):
        """ observed window time interval. """
        return self.last_update == self.history[-1][0]

    def __str__(self):
        return "%s:\t%d BR (%.1f sec/BR) [%s]" % (
            self.name, self.count, self.rate, self.window_size
        )


class RedisStatReader(object):
    REDIS_KEY_SET_REFRESH = 15 # seconds
    REDIS_CONNECTION_TIMEOUTS = [15, 30, 60, 120, 240] # seconds

    def __init__(self, redis, key_set):
        self.redis = redis
        self.key_set = key_set
        self.keys = []
        self.daemon_ids = []
        self._keys_last_update = -inf # never

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
                    print_error("Cannot connect to the Redis server! (%s)" % error)
                    self._redis_connection_trial += 1
                    timeout = self.connection_timeout
                    if self._terminated.wait(timeout):
                        raise self.Terminated
                else:
                    self._redis_connection_trial = 0
                    return result
        return _redis_call_wrapper

    def read_stat(self):
        self._update_keys()
        return self._read_stat()

    @_redis_call
    def _read_stat(self):
        """ Read pipe sizes. """
        daemon_ids, queue_ids = self.daemon_ids, self.keys
        pipeline = self.redis.pipeline()
        for daemon_id in daemon_ids:
            pipeline.get(STATUS_KEY_PREFIX + daemon_id)
            pipeline.llen(BUFFER_KEY_PREFIX + daemon_id)
            pipeline.hlen(JOBS_KEY_PREFIX + daemon_id)
        for key in queue_ids:
            pipeline.llen(key)
        result = pipeline.execute()
        return {
            "daemons": [
                {
                    "id": id_,
                    "status": result[3*idx+0],
                    "buffer": result[3*idx+1],
                    "jobs": result[3*idx+2],
                } for idx, id_ in enumerate(daemon_ids)
            ],
            "queues": zip(queue_ids, result[3*len(daemon_ids):])
        }

    @_redis_call
    def _update_keys(self):
        """ Update the list of the watched ingestion queues (Redis keys). """
        if (time() - self._keys_last_update) < self.REDIS_KEY_SET_REFRESH:
            return

        pipeline = self.redis.pipeline()
        pipeline.smembers(self.key_set)
        pipeline.keys(pattern=(BROWSEWATCHD_KEY_PREFIX + "*:*"))
        result = pipeline.execute()
        self.keys = tuple(sorted(result[0] | set(EXTRA_KYES)))

        def _extract_daemon_ids(keys):
            "Extract daemons' ids from daemons' keys"
            for key in keys:
                match = RE_DAEMON_KEY_PATTERN.match(key)
                if match:
                    yield match.groupdict()['daemon_id']

        self.daemon_ids = tuple(sorted(set(_extract_daemon_ids(result[1]))))


def write_log(log_file, state):
    if state.changed:
        with open(log_file, "a") as fout:
            fout.write(
                "%.3f\t%s\t%d\t%4g\n" % (
                    state.last_update,
                    state.name,
                    state.count,
                    state.rate
                )
            )

def ingestion_stat(redis_host, redis_port, redis_key_set, log_file):

    def _format_br_count(count):
        return "%12d BR" % count

    def _format_br_rate(rate):
        return "%8.1f s/BR" % rate

    def _format_timestamp(timestamp):
        dt = datetime.utcfromtimestamp(ceil(timestamp))
        return dt.isoformat("T") + "Z"

    def _render_daemon(id, status, jobs, buffer, **kwargs):
        screen.write_line("\tdaemon status:\t%s" % status)
        screen.write_line("\tdaemon name:\t%s" % id)
        screen.write_line("\tbuffered BRs:\t%s" % _format_br_count(buffer))
        screen.write_line("\tjobs in progress:\t%s" % _format_br_count(jobs))
        screen.write_line("")

    def _render_qstate(qstate):
        #screen.write_line("\t".join([str(i) * 30 for i in range(10)]))
        line = "\t%s\t%s" % (qstate.name, _format_br_count(qstate.count))
        if qstate.count > 0 and len(qstate.history) > 1:
            line += "\t%s\t%s\t%s" % (
                _format_br_rate(qstate.rate),
                _format_timestamp(qstate.completion_estimate),
                "[%3.0f%%]" % (100*qstate.window_size),
            )
        screen.write_line(line)

    def _render(state):
        screen.clear()
        screen.write_line(" --= browsewatchd monitor =-- ")
        screen.write_line("")
        if state['daemons']:
            screen.write_line("daemons:")
            screen.write_line("")
        for dstate in state['daemons']:
            _render_daemon(**dstate)
        screen.write_line("queues (%s):" % redis_key_set)
        screen.write_line("")

        _render_qstate(state['total_queue_states'])
        qstates = [
            qstate for name, qstate in sorted(state['queue_states'].items())
            if qstate.count > 0
        ]
        if qstates:
            screen.write_line("\t---")
        for qstate in qstates:
            _render_qstate(qstate)
        screen.refresh()
        return 
        screen.write_line("daemon_status: %s" % (daemon_state['status'] or "n/a"))
        for state in [total_state, buffer_state, jobs_state]:
            screen.write_line(state)
            write_log(log_file, state)

        for state in pipe_state.values():
            screen.write_line(state)
            write_log(log_file, state)

        screen.refresh()

    stat_reader = RedisStatReader(
        redis=Redis(host=redis_host, port=redis_port),
        key_set=redis_key_set,
    )

    screen = CScreen()
    screen.tabs = [2, 24, 16, 16, 24, 12]

    total_state = None
    queue_state = {}

    while True:
        state = stat_reader.read_stat()

        # reset state if no daemon is running
        n_running = sum(1 for dstate in state['daemons'] if dstate['status'] == "RUNNING")
        if state['daemons'] and not n_running: # workaround for the old browsewatch.sh
        #if not n_running:
            total_state = None
            total_state = QueueState("TOTAL")
            queue_state = {}

        # count buffered items
        total = 0
        for dstate in state['daemons']:
            total = dstate['buffer']

        for name, count in state['queues']:
            total += count
            if name not in queue_state:
                queue_state[name] = QueueState(name, count)
            else:
                queue_state[name].update(count)
        if total_state is None:
            total_state = QueueState("TOTAL", total)
        else:
            total_state.update(total)

        state['queue_states'] = dict(queue_state)
        state['total_queue_states'] = total_state

        _render(state)

        sleep(1)


def main(*args):
    try:
        kwargs = parse_args(*args)
        ingestion_stat(**kwargs)
    except CommandError as error:
        print_error(str(error))
        return 1
    finally:
        curses.endwin()
    return 0


def parse_args(*args):
    """ Parse CLI argument. """
    # collection list is a Redis set containing the current list of browse
    # report ingestion queues
    collection_list = None
    log_file = DEF_LOGFILE
    redis_host = DEF_REDIS_HOST
    redis_port = DEF_REDIS_PORT

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
            elif option in ("-log", "--log", "--log-file"):
                log_file = next(it_args)
                if not log_file:
                    raise ValueError("Invalid log file path!")
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

    return dict(
        redis_host=redis_host,
        redis_port=redis_port,
        redis_key_set=collection_list,
        log_file=log_file,
    )


def print_usage(execname):
    """ print command usage """
    print(
        "USAGE: %s "
        "[--host <redis-host>]"
        "[--port <redis-port>]"
        "[--log-file <log-file>] "
        "[<redis-collection-list>]"
        "" % basename(execname),
        file=sys.stderr
    )


def print_error(message):
    """ print error message """
    print("ERROR: %s" % message, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
