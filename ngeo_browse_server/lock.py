#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

import os
import errno
import time
from functools import wraps


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
                    raise LockException("Could not acquire lock for file '%s' "
                                        "within timeout." % self.lockfile)
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


def file_locked(lockfile, timeout=None, delay=.05):
    """ Decorator to secure a function with a file lock.
    """

    def outer_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with FileLock(lockfile, timeout, delay):
                return func(*args, **kwargs)
        return wrapper
    return outer_wrapper
