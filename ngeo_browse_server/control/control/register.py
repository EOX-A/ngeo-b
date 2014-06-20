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

import os
from os.path import exists
from ConfigParser import ConfigParser

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.lock import FileLock, LockException
from ngeo_browse_server.control.control.config import (
    get_instance_id, get_controller_config_path, 
    get_controller_config_lockfile_path, 
    get_controller_config, create_controller_config
)
from ngeo_browse_server.control.control.assertion import (
    assert_instance_id, assert_instance_type, assert_controller_id,
    assert_controller_ip, ControllerAssertionError
)


def register(instance_id, instance_type, cs_id, cs_ip, config=None):
    config = config or get_ngeo_config()
    assert_instance_id(instance_id, config)
    assert_instance_type(instance_type)

    try:
        with FileLock(get_controller_config_lockfile_path(config)):
            controller_config_path = get_controller_config_path(config)
            if not exists(controller_config_path):
                create_controller_config(controller_config_path, cs_id, cs_ip)
            else:
                controller_config = get_controller_config(controller_config_path)

                assert_controller_id(cs_id, controller_config, "ALREADY_OTHER")
                assert_controller_ip(cs_ip, controller_config)

    except LockException:
        raise ControllerAssertionError(
            "There is currently another registration in progress.",
            reason="ALREADY_OTHER"
        )


def unregister(instance_id, cs_id, cs_ip, config=None):
    config = config or get_ngeo_config()
    assert_instance_id(instance_id, config)

    try:
        with FileLock(get_controller_config_lockfile_path(config)):
            controller_config_path = get_controller_config_path(config)
            if not exists(controller_config_path):
                raise ControllerAssertionError(
                    "This Browse Server instance was not yet registered.",
                    reason="UNBOUND"
                )

            controller_config = get_controller_config(controller_config_path)
            assert_controller_id(cs_id, controller_config, "CONTROLLER_OTHER")
            assert_controller_ip(cs_ip, controller_config)
            
            # remove the controller configuration to complete unregistration
            os.remove(controller_config_path)

    except LockException:
        raise ControllerAssertionError(
            "There is currently another registration in progress.",
            reason="CONTROLLER_OTHER"
        )
