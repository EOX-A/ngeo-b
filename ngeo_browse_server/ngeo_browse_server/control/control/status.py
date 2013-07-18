
from ngeo_browse_server.lock import FileLock
from ngeo_browse_server.control.control.config import (
    get_status_config_path, get_status_config_lockfile_path
)

def get_status(config=None):
    config = config or get_ngeo_config()
    return Status(config)


# decorator
class locked(object):
    def __init__(self, fn, timeout=None):
        self.fn = fn
        self.timeout = timeout

    def __call__(self, *args, **kwargs):
        config = config or get_ngeo_config()
        lockfile = get_status_config_lockfile_path()
        with FileLock(lockfile, self.timeout):
            return self.fn(*args, **kwargs)


class Status(object):

    commands = frozenset(("pause", "resume", "start", "shutdown", "restart"))

    def __init__(self, config=None):
        self.config = config or get_ngeo_config()

    def command(self, command):
        command = command.lower()

        if command in self.commands:
            return getattr(self, command)()

    @locked
    def pause(self):
        pass

    @locked
    def resume(self):
        pass

    @locked
    def start(self):
        pass

    @locked
    def shutdown(self):
        pass

    @locked
    def restart(self):
        pass

    @locked
    def __str__(self):
        pass        
