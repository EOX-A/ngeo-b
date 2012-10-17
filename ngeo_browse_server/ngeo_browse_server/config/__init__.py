from os.path import join
from django.conf import settings

from ConfigParser import ConfigParser


_config_instance = None


def get_ngeo_config():
    global _config_instance 
    if not _config_instance:
        _config_instance = ConfigParser()
        _config_instance.read([join(settings.PROJECT_DIR, "conf", "ngeo.conf"),
                               ]) # TODO: read default conf?
    
    return _config_instance
    
        
    
    




