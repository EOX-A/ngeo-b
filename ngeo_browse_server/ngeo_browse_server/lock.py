import os
import errno


class LockException(Exception):
    pass


class FileLock(object):
    """ Generic lock using an exclusive file in the file system for 
        synchronization. 
    """
    
    def __init__(self, lockfile=None):
        self.lockfile = lockfile
        self.is_locked = False

    def acquire(self):
        """ Acquire the lock, if possible. Raises an OSError if not. """
        try:
            self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise LockException
        self.is_locked = True

    def release(self):
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False

    def __enter__(self):
        # TODO: create and open lockfile with exclusive access
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, *args):
        self.release()
