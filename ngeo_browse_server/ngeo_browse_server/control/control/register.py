
from ConfigParser import ConfigParser

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.control.config import (
    get_instance_id, get_controller_config_path
)


SEC_CONTROLLER = "controller_server"


class LockException(Exception):
    pass

class RegistrationLock(object):
    def __init__(self, lockfile=None):
        self.lockfile = lockfile
        self.is_locked = False

    def acquire(self):
        """ Acquire the lock, if possible. Raises an OSError if not. """
        try:
            self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise LockException
        self.is_locked = True

    def release(self):
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False

    def __enter__(self):
        # TODO: create and open lockfile with exclusive access
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, *args):
        self.release()




def register(instance_id, instance_type, cs_id, cs_ip, config=None):
    # TODO: get actual instance ID
    config = config or get_ngeo_conf()
    actual_instance_id = get_instance_id(config)

    if instance_id != actual_instance_id:
        raise RegistrationException(
            "The provided instance ID (%s) is not the same as the configured "
            "one (%s)." % (instance_id, actual_instance_id),
            reason="INSTANCE_OTHER", instance_id=actual_instance_id
        )

    if instance_type != "BrowseServer":
        raise RegistrationException(
            "The provided instance ID (%s) is not the same as the configured "
            "one (%s)." % (instance_id, actual_instance_id),
            reason="TYPE_OTHER", instance_id=actual_instance_id
        )

    try:
        with RegistrationLock(get_registration_lockfile(config)):
            controller_config_path = get_controller_config_path(config)
            if not os.exists(controller_config_path):
                create_controller_config(controller_config_path, cs_id, cs_ip)
            else:
                controller_config = get_controller_config(controller_config_path)
                actual_id = controller_config.get(SEC_CONTROLLER, "identifier")
                actual_ip = controller_config.get(SEC_CONTROLLER, "address")

                if actual_id != cs_id:
                    raise RegistrationException(
                        "This browse server instance is already registered on "
                        "the controller server with ID '%s'." % (actual_id),
                        reason="ALREADY_OTHER", instance_id=instance_id
                    )

                elif actual_ip != cs_ip:
                    raise RegistrationException(
                        "This browse server instance is registered on a "
                        "controller server with the same ID but another "
                        "IP-address ('%s')." % actual_ip,
                        reason="INTERFACE_OTHER", instance_id=instance_id
                    )




    except LockException:
        raise RegistrationException(
            "There is currently another registration in progress."
            reason="ALREADY_OTHER", instance_id=instance_id
        )


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

