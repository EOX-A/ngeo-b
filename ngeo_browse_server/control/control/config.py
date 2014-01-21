#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

from ConfigParser import ConfigParser

from ngeo_browse_server.config import (
    get_ngeo_config, get_project_relative_path, safe_get
)


logger = logging.getLogger(__name__)

CTRL_SECTION = "control"
CONTROLLER_SERVER_SECTION = "controller_server"
STATUS_SECTION = "status"

def get_instance_id(config=None):
    config = config or get_ngeo_config()
    return config.get(CTRL_SECTION, "instance_id")


def get_controller_config_path(config=None):
    """ Returns the configured failure directory. """
    
    config = config or get_ngeo_config()

    return get_project_relative_path(
        config.get(CTRL_SECTION, "controller_config_path")
    )



def get_controller_config_lockfile_path(config=None):
    config = config or get_ngeo_config()

    return get_controller_config_path(config) + ".lck"


def get_status_config_path(config=None):
    """ Returns the configured failure directory. """
    
    config = config or get_ngeo_config()

    return get_project_relative_path(
        config.get(CTRL_SECTION, "status_config_path", "config/status")
    )


def get_status_config_lockfile_path(config=None):
    config = config or get_ngeo_config()

    return get_status_config_path(config) + ".lck"


# controller server config only


def create_controller_config(controller_config_filename, cs_id, cs_ip):
    parser = ConfigParser()    
    parser.add_section(CONTROLLER_SERVER_SECTION)
    parser.set(CONTROLLER_SERVER_SECTION, "identifier", cs_id)
    parser.set(CONTROLLER_SERVER_SECTION, "address", cs_ip)
    with open(controller_config_filename, "w") as f:
        parser.write(f)


def get_controller_config(controller_config_filename):
    parser = ConfigParser() 
    with open(controller_config_filename, "r") as f:
        parser.readfp(f)
    return parser


# status stuff


def create_status_config(status_config_filename):
    parser = ConfigParser()    
    parser.add_section(STATUS_SECTION)
    parser.set(STATUS_SECTION, "state", "RUNNING")
    with open(status_config_filename, "w") as f:
        parser.write(f)


# log reporting stuff

def get_configured_log_file_patterns(config):
    config = config or get_ngeo_config()

    items = safe_get(config, CTRL_SECTION, "report_log_files")
    if items is None:
        return []

    return map(get_project_relative_path, items.split(","))
