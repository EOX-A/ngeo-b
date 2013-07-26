from os.path import getmtime, basename
from glob import glob
from datetime import date

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.control.config import (
    get_configured_log_file_patterns
)


def date_of_file(filename):
    return date.fromtimestamp(getmtime(filename))


def get_log_files(config=None):
    files = {}

    for pattern in get_configured_log_file_patterns(config):
        for logfile in glob(pattern):
            #logfile = basename(logfile)
            files.setdefault(date_of_file(logfile), set()).add(pattern)

    return files





#
>>> time.mktime(d.timetuple())
1374552000.0
>>> os.utime("/var/ngeob/autotest/logs/ngeo.log.1", (1374552000,1374552000))



