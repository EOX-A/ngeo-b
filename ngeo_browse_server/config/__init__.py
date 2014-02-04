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

import os
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

def write_ngeo_config():
    """ Writes the current ngeo config to the config file.
    """
    
    global _config_instance

    with open(get_ngeo_config_path(), "w") as f:
        _config_instance.write(f)



def reset_ngeo_config():
    """ Reset the global configuration instance and reread the contents from the 
    config file. """
    
    global _config_instance
    _config_instance = ConfigParser()
    _config_instance.read([get_ngeo_config_path(),])


def get_ngeo_config_path():
    """ Get the absolute path to the current ngeo config file. This is either
        the ``NGEO_CONFIG_FILE`` environment variable, or 
        $PROJECT_DIR/conf/ngeo.conf.
    """

    return join(settings.PROJECT_DIR, "conf", "ngeo.conf")
    #return os.environ.get(
    #    "NGEO_CONFIG_FILE", 
    #    
    #)


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
