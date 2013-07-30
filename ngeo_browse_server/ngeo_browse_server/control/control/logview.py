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

    patterns = get_configured_log_file_patterns(config)

    for pattern in patterns:
        for logfile in glob(pattern):
            files.setdefault(
                date_of_file(logfile), set()
            ).add(logfile)

    return files


def get_log_file(date, name, config=None):
    files = get_log_files(config)

    try:
        for path in files[date]:
            if name == basename(path):
                return path
    except KeyError:
        pass
    return None


