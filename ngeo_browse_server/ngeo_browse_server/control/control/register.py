
from ConfigParser import ConfigParser

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.lock import FileLock, LockException
from ngeo_browse_server.control.control.config import *
from ngeo_browse_server.control.control.assertion import *


SEC_CONTROLLER = "controller_server"


def register(instance_id, instance_type, cs_id, cs_ip, config=None):
    config = config or get_ngeo_conf()
    actual_instance_id = get_instance_id(config)

    assert_instance_id(instance_id, config)
    assert_instance_type(instance_type)

    try:
        with FileLock(get_registration_lockfile(config)):
            controller_config_path = get_controller_config_path(config)
            if not os.exists(controller_config_path):
                create_controller_config(controller_config_path, cs_id, cs_ip)
            else:
                # TODO: controller server ID was removed?
                controller_config = get_controller_config(controller_config_path)

                assert_controller_id(cs_id, controller_config)
                assert_controller_ip(cs_id, controller_config)

    except LockException:
        raise RegistrationException(
            "There is currently another registration in progress."
            reason="ALREADY_OTHER", instance_id=instance_id
        )


def unregister(instance_id, cs_id, cs_ip, config=None):
    config = config or get_ngeo_conf()
    actual_instance_id = get_instance_id(config)

    assert_instance_id(instance_id, config)
    # TODO: no type?

    try:
        with FileLock(get_registration_lockfile(config)):
            controller_config_path = get_controller_config_path(config)
            if not os.exists(controller_config_path):
                raise RegistrationException(
                    "This browse server instance was not yet registered.",
                    reason="UNBOUND", instance_id=instance_id
                )

            # TODO: controller server ID was removed?
            controller_config = get_controller_config(controller_config_path)
            assert_controller_id(cs_id, controller_config)
            assert_controller_ip(cs_ip, controller_config)
            
            # remove the controller configuration to complete unregistration
            os.remove(controller_config_path)

    except LockException:
        raise RegistrationException(
            "There is currently another registration in progress."
            reason="ALREADY_OTHER", instance_id=instance_id
        )
