from os.path import isabs, join, basename, splitext
from ConfigParser import NoSectionError, NoOptionError

from django.conf import settings

from ngeo_browse_server.config import get_ngeo_config, safe_get


def get_project_relative_path(path):
    if isabs(path):
        return path
    
    return join(settings.PROJECT_DIR, path)


def get_storage_path(file_name, storage_dir=None):
    """ Returns an absolute path to a filename within the intermediary storage
    directory for uploaded but unprocessed files. 
    """
    
    section = "control.ingest"
    
    if not storage_dir:
        storage_dir = get_ngeo_config().get(section, "storage_dir")
    
    return get_project_relative_path(join(storage_dir, file_name))


def get_optimized_path(file_name, optimized_dir=None):
    """ Returns an absolute path to a filename within the storage directory for
    optimized raster files. Uses the optimized directory if given, otherwise 
    uses the 'control.ingest.optimized_files_dir' setting from the ngEO
    configuration.
    
    Also tries to get the postfix for optimized files from the 
    'control.ingest.optimized_files_postfix' setting from the ngEO configuration.
    
    All relative paths are treated relative to the PROJECT_DIR directory setting.
    """
    file_name = basename(file_name)
    config = get_ngeo_config()
    
    section = "control.ingest"
    
    if not optimized_dir:
        optimized_dir = config.get(section, "optimized_files_dir")
        
    optimized_dir = get_project_relative_path(optimized_dir)
    
    try:
        postfix = config.get(section, "optimized_files_postfix")
    except NoSectionError, NoOptionError:
        postfix = ""
    
    root, ext = splitext(file_name)
    return join(optimized_dir, root + postfix + ext)


def get_format_config():
    values = {}
    config = get_ngeo_config()
    
    section = "control.ingest"
    
    values["compression"] = safe_get(config, section, "compression")
    
    if values["compression"] == "JPEG":
        value = safe_get(config, section, "jpeg_quality")
        values["jpeg_quality"] = int(value) if value is not None else None
    
    elif values["compression"] == "DEFLATE":
        value = safe_get(config, section, "zlevel")
        values["zlevel"] = int(value) if value is not None else None
        
    try:
        values["tiling"] = config.getboolean(section, "tiling")
    except: pass
    
    return values


def get_optimization_config():
    values = {}
    config = get_ngeo_config()
    
    section = "control.ingest"
    
    try:
        values["overviews"] = config.getboolean(section, "overviews")
    except: pass
    
    try:
        values["color_index"] = config.getboolean(section, "color_index")
    except: pass
    
    try:
        values["footprint_alpha"] = config.getboolean(section, "footprint_alpha")
    except: pass
    
    return values


def get_mapcache_config():
    values = {}
    config = get_ngeo_config()
    
    section = "control.ingest.mapcache"
    
    values["seed_command"] = config.get(section, "seed_command")
    values["config_file"] = config.get(section, "config_file")
    values["threads"] = int(safe_get(config, section, "threads", 1))
    
    return values