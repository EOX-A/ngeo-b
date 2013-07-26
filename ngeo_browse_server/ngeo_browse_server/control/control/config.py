from ConfigParser import ConfigParser

from ngeo_browse_server.config import (
    get_ngeo_config, get_project_relative_path, safe_get
)


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

    patterns = safe_get(config, CTRL_SECTION, "report_log_files")
    if patterns is None:
        return []

    return map(get_project_relative_path, patterns.split(","))
