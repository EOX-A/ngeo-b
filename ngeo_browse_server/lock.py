import os
import errno
import time


class LockException(Exception):
    pass


class FileLock(object):
    """ Generic lock using an exclusive file in the file system for 
        synchronization. 
    """
    
    def __init__(self, lockfile=None, timeout=None, delay=.05):
        self.lockfile = lockfile
        self.fd = None

        self.timeout = timeout
        self.delay = delay
    
    @property
    def is_locked(self):
        """ See if we are currently locking the lock file. """
        return self.fd is not None

    def acquire(self):
        """ Acquire the lock, if possible. Raises a LockException if not. """

        if self.is_locked:
            return

        begin = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise 
                if not self.timeout or (time.time() - begin) >= self.timeout:
                    raise LockException("File is locked.")
                time.sleep(self.delay)

    def release(self):
        """ Release the lock by deleting the lock file. """
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.fd = None

    def __enter__(self):
        """ Context guard entry. """
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, *args):
        """ Context guard exit. """
        self.release()

    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()

    