from ConfigParser import ConfigParser

from ngeo_browse_server.config import (
    get_ngeo_config, get_project_relative_path
)


CTRL_SECTION = "control"
CONTROLLER_SERVER_SECTION = "controller_server"

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




