
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


