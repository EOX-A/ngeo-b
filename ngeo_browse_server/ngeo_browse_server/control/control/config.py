
from ngeo_browse_server.config import (
    get_ngeo_config, get_project_relative_path
)


CTRL_SECTION = "control"

def get_instance_id(config=None):
    config = config or get_ngeo_config()
    return config.get(CTRL_SECTION, "instance_id")


def get_controller_config_path(config=None):
    """ Returns the configured failure directory. """
    
    config = config or get_ngeo_config()

    return get_project_relative_path(
        config.get(CTRL_SECTION, "controller_config_path")
    )


# controller server config only


def create_controller_config(controller_config_filename, cs_id, cs_ip):
    parser = ConfigParser()    
    parser.add_section(SEC_CONTROLLER)
    parser.set(SEC_CONTROLLER, "identifier", cs_id)
    parser.set(SEC_CONTROLLER, "address", cs_ip)
    with open(controller_config_filename, "w") as f:
        parser.write(f)


def get_controller_config(controller_config_filename):
    parser = ConfigParser() 
    with open(controller_config_filename, "r") as f:
        parser.read(f)
    return parser




