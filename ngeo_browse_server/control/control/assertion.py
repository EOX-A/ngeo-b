#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

from ngeo_browse_server.control.control.config import (
    get_instance_id, CONTROLLER_SERVER_SECTION
)


class ControllerAssertionError(AssertionError):
    def __init__(self, message, reason):
        super(ControllerAssertionError, self).__init__(message)
        self.reason = reason


def assert_instance_id(instance_id, config):
    actual_instance_id = get_instance_id(config)

    if instance_id != actual_instance_id:
        raise ControllerAssertionError(
            "The provided instance ID (%s) is not the same as the configured "
            "one (%s)." % (instance_id, actual_instance_id),
            reason="INSTANCE_OTHER"
        )


def assert_instance_type(instance_type):
    if instance_type != "BrowseServer":
        raise ControllerAssertionError(
            "The provided instance type '%s' is not 'BrowseServer'." % 
            (instance_type), reason="TYPE_OTHER"
        )


def assert_controller_id(cs_id, controller_config, reason):
    actual_id = controller_config.get(CONTROLLER_SERVER_SECTION, "identifier")

    if actual_id != cs_id:
        raise ControllerAssertionError(
            "This browse server instance is registered on the "
            "controller server with ID '%s'." % (actual_id),
            reason=reason # because its currently different in register/unregister
        )


def assert_controller_ip(cs_ip, controller_config):
    actual_ip = controller_config.get(CONTROLLER_SERVER_SECTION, "address")

    if actual_ip != cs_ip:
        raise ControllerAssertionError(
            "This browse server instance is registered on a "
            "controller server with the same ID but another "
            "IP-address ('%s')." % actual_ip,
            reason="INTERFACE_OTHER"
        )
