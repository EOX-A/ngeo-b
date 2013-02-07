#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
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


import logging
import tempfile
import shutil
from os import remove
from os.path import exists


logger = logging.getLogger(__name__)

#===============================================================================
# Ingestion Transaction
#===============================================================================

class FileTransaction(object):
    """ File Transaction guard to save previous files for a critical section to
    be used with the "with"-statement.
    """
    
    def __init__(self, *subject_filenames):
        self._subject_filenames = subject_filenames
    
    
    def __enter__(self):
        " Start of critical block. Check if file exists and create backup. "
        
        # save a reference to the original file (key) and its backup (value).
        self._file_map = {}
        
        # check if the file in question exists. If it does, move it to a safe 
        # location.
        existing_filenames = [filename for filename in set(self._subject_filenames)
                              if filename and exists(filename)]
        
        for filename in existing_filenames:
            _, self._file_map[filename] = tempfile.mkstemp()
            logger.debug("Generating backup file for '%s'." % filename)
            
            shutil.move(filename, self._file_map[filename])
        
    
    
    def __exit__(self, etype, value, traceback):
        " End of critical block. Either revert changes or delete backup. "

        # on success
        if (etype, value, traceback) == (None, None, None):
            # delete all backups because no error occurred
            logger.debug("Removing backups because no error occurred.")
            for filename, backup_filename in self._file_map.items():
                logger.debug("Remove backup for '%s'." % filename)
                remove(backup_filename)
        
        # on error
        else:
            # try removing the new file because an error occurred. It may not exist.
            logger.debug("Performing rollback because an error occurred.")
            for filename in set(self._subject_filenames):
                try:
                    remove(filename)
                    logger.debug("Deleting '%s'." % filename)
                except (OSError, TypeError):
                    pass
            
            # restore all backups
            for filename, backup_filename in self._file_map.items():
                logger.debug("Restoring backup for '%s'." % filename)
                shutil.move(backup_filename, filename)
