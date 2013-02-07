from os.path import isabs, join
from django.conf import settings

from ConfigParser import ConfigParser


_config_instance = None


def get_ngeo_config():
    """ Return the global configuration instance. Initialize it, if it has not 
    yet been done."""
    
    global _config_instance 
    if not _config_instance:
        reset_ngeo_config()
    
    return _config_instance


def reset_ngeo_config():
    """ Reset the global configuration instance and reread the contents from the 
    config file. """
    
    global _config_instance
    _config_instance = ConfigParser()
    _config_instance.read([join(settings.PROJECT_DIR, "conf", "ngeo.conf"),
                           ])


def safe_get(config, section, option, default=None):
    """ Convenience function to get a value from a config or retrieve the 
    default.
    """
    
    try:
        return config.get(section, option)
    except:
        return default


def get_project_relative_path(path):
    """ Returns a path, relative to the defined `PROJECT_DIR` directory. """
    
    if isabs(path):
        return path
    
    return join(settings.PROJECT_DIR, path)
