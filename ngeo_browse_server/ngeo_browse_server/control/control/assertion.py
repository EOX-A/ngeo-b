
def assert_instance_id(instance_id, config):
    actual_instance_id = get_instance_id(config)

    if instance_id != actual_instance_id:
        raise RegistrationException(
            "The provided instance ID (%s) is not the same as the configured "
            "one (%s)." % (instance_id, actual_instance_id),
            reason="INSTANCE_OTHER", instance_id=actual_instance_id
        )


def assert_instance_type(instance_type, config):
    instance_id = get_instance_id(config)

    if instance_type != "BrowseServer":
        raise RegistrationException(
            "The provided instance type '%s' is not 'BrowseServer'." % 
            (instance_type),
            reason="TYPE_OTHER", instance_id=instance_id
        )


def assert_controller_id(cs_id, controller_config, config):
    instance_id = get_instance_id(config)
    actual_id = controller_config.get(SEC_CONTROLLER, "identifier")

    if actual_id != cs_id:
        raise RegistrationException(
            "This browse server instance is registered on the "
            "controller server with ID '%s'." % (actual_id),
            reason="CONTROLLER_OTHER", instance_id=instance_id # TODO: check if this is different from `register`s ALREADY_OTHER
        )


def assert_controller_ip(cs_ip, controller_config, config):
    instance_id = get_instance_id(config)
    actual_ip = controller_config.get(SEC_CONTROLLER, "address")

    if actual_ip != cs_ip:
        raise RegistrationException(
            "This browse server instance is registered on a "
            "controller server with the same ID but another "
            "IP-address ('%s')." % actual_ip,
            reason="INTERFACE_OTHER", instance_id=instance_id
        )
