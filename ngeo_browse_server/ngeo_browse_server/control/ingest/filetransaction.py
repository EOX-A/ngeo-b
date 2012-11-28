import logging
import tempfile
import shutil
from os import remove
from os.path import exists


logger = logging.getLogger(__name__)

#===============================================================================
# Ingestion Transaction
#===============================================================================

class IngestionTransaction(object):
    """ File Transaction guard to save previous files for a critical section to
    be used with the "with"-statement.
    """
    
    def __init__(self, subject_filename, safe_filename=None):
        self._subject_filename = subject_filename
        self._safe_filename = safe_filename
    
    
    def __enter__(self):
        " Start of critical block. Check if file exists and create backup. "
        
        # check if the file in question exists. If it does, move it to a safe 
        # location 
        self._exists = exists(self._subject_filename)
        if not self._exists:
            # file does not exist, do nothing
            logger.debug("File '%s' does not exist, do nothing."
                         % self._subject_filename)
            return
        
        # create a temporary file if no path was given
        if not self._safe_filename:
            _, self._safe_filename = tempfile.mkstemp()
            logger.debug("Generating backup file '%s'." % self._safe_filename)
        
        logger.debug("Moving '%s' to '%s'." 
                     % (self._subject_filename, self._safe_filename))
        
        # move the old file to a safe location
        shutil.move(self._subject_filename, self._safe_filename)
    
    
    def __exit__(self, etype, value, traceback):
        " End of critical block. Either revert changes or delete backup. "

        if (etype, value, traceback) == (None, None, None):
            # no error occurred
            logger.debug("No error occurred.")
            if self._exists:
                # delete the saved old file, if it existed
                logger.debug("Deleting backup '%s'." % self._safe_filename)
                remove(self._safe_filename)
        
        # on error
        else:
            # an error occurred, try removing the new file. It may not exist.
            try:
                logger.debug("An error occurred, deleting '%s'."
                             % self._subject_filename)
                remove(self._subject_filename)
            except OSError:
                pass
            
            # move the backup file back to restore the initial condition
            if self._exists:
                logger.debug("Restoring backup '%s'." % self._safe_filename)
                shutil.move(self._safe_filename, self._subject_filename)
