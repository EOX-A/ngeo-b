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
    states = frozenset(("RUNNING", "RESUMING", "PAUSING", "PAUSED", "STARTING", "SHUTTING_DOWN"))

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
            raise StatusError("To 'pause', the server needs to be 'running'.")
        self._set_status("PAUSED")

    @locked()
    def resume(self):
        if self._get_status() != "PAUSED":
            raise StatusError("To 'resume', the server needs to be 'paused'.")
        self._set_status("RUNNING")

    #@locked()
    #def start(self):
    #    self._set_status("running")#

    #@locked()
    #def shutdown(self):
    #    self._set_status("shutting_down")

    #@locked()
    #def restart(self):
    #    self._set_status("running")

    @locked(timeout=1.)
    def state(self):
        return self._get_status()

    def __str__(self):
        return self.state()

    @property
    @locked()
    def running(self):
        return self._get_status() == "RUNNING"
