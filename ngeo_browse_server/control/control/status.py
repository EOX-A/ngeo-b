#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from os.path import exists
from ConfigParser import ConfigParser
from functools import wraps

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.lock import FileLock
from ngeo_browse_server.control.control.config import (
    get_status_config_path, get_status_config_lockfile_path, 
    write_status_config, STATUS_SECTION
)


class StatusError(Exception):
    pass


def get_status(config=None):
    """ Convenience function to return a `Status` object with the global 
        configuration. 
    """

    config = config or get_ngeo_config()
    return Status(config)


def locked(timeout=None):
    """ Decorator for methods that shall lock the status configuration.
    """
    
    def wrap_fn(fn):
        @wraps(fn)
        def wrap_call(*args, **kwargs):
            config = get_ngeo_config()
            lockfile = get_status_config_lockfile_path()
            with FileLock(lockfile, timeout):
                return fn(*args, **kwargs)
        #return LockGuard(fn, timeout)
        return wrap_call
    return wrap_fn


class Status(object):

    commands = frozenset(("pause", "resume", "start", "shutdown", "restart"))
    states = frozenset(("RUNNING", "RESUMING", "PAUSING", "PAUSED", "STARTING", "STOPPED"))

    def __init__(self, config=None):
        self.config = config or get_ngeo_config()


    def _status_config(self):
        status_config_path = get_status_config_path(self.config)
        if not exists(status_config_path):
            write_status_config(status_config_path)

        parser = ConfigParser()
        with open(status_config_path) as f:
            parser.readfp(f)
        return parser

    
    def _set_status(self, new_status):
        new_status = new_status.upper()
        if not new_status in self.states:
            raise ValueError("Invalid state '%s'." % new_status)

        status_config = self._status_config()

        if not status_config.has_section(STATUS_SECTION):
            status_config.add_section(STATUS_SECTION)
        status_config.set(STATUS_SECTION, "state", new_status)
        write_status_config(get_status_config_path(self.config), status_config)


    def _get_status(self):
        status_config = self._status_config()
        return status_config.get(STATUS_SECTION, "state").upper()


    def command(self, command):
        command = command.lower()

        if command in self.commands:
            return getattr(self, command)()

        raise AttributeError

    @locked()
    def pause(self):
        if self._get_status() != "RUNNING":
            raise StatusError("To 'pause', the server needs to be 'RUNNING'.")
        self._set_status("PAUSED")

    @locked()
    def resume(self):
        if self._get_status() != "PAUSED":
            raise StatusError("To 'resume', the server needs to be 'PAUSED'.")
        self._set_status("RUNNING")

    @locked()
    def start(self):
        if self._get_status() != "STOPPED":
            raise StatusError("To 'start', the server needs to be 'STOPPED'.")
        self._set_status("RUNNING")

    @locked()
    def shutdown(self):
        if self._get_status() != "RUNNING":
            raise StatusError("To 'shutdown', the server needs to be 'RUNNING'.")
        self._set_status("STOPPED")

    @locked()
    def restart(self):
        if self._get_status() != "STOPPED":
            raise StatusError("To 'restart', the server needs to be 'STOPPED'.")
        self._set_status("RUNNING")

    @locked(timeout=1.)
    def state(self):
        return self._get_status()

    def __str__(self):
        return self.state()

    @property
    @locked()
    def running(self):
        return self._get_status() == "RUNNING"
