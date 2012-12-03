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
            # no error occurred, delete all backups
            logger.debug("No error occurred, removing backups.")
            for filename, backup_filename in self._file_map.items():
                logger.debug("Remove backup for '%s'." % filename)
                remove(backup_filename)
        
        # on error
        else:
            # an error occurred, try removing the new file. It may not exist.
            logger.debug("An error occurred, deleting generated files.")
            for filename in set(self._subject_filenames):
                try:
                    logger.debug("Deleting '%s'." % filename)
                    remove(filename)
                except (OSError, TypeError):
                    pass
            
            # restore all backups
            for filename, backup_filename in self._file_map.items():
                logger.debug("Restoring backup for '%s'." % filename)
                shutil.move(backup_filename, filename)
