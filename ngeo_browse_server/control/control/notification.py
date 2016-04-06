#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 European Space Agency
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
import threading
import urllib2
import traceback
from ConfigParser import NoSectionError

from lxml import etree
from lxml.builder import E
from django.utils.timezone import now
from eoxserver.core.util.timetools import isotime

from ngeo_browse_server.config import get_ngeo_config, safe_get
from ngeo_browse_server.control.control.config import (
    get_controller_config, get_controller_config_path, get_instance_id,
    CONTROLLER_SERVER_SECTION
)


logger = logging.getLogger(__name__)


def notify(summary, message, urgency=None, ip_address=None, config=None):
    config = config or get_ngeo_config()

    urgency = urgency or "INFO"
    if urgency not in ("INFO", "CRITICAL", "BLOCK"):
        raise ValueError("Invalid urgency value '%s'." % urgency)

    try:
        if not ip_address:
            # get the value for "notification_url" and fall back to
            # "address"
            ip_address = safe_get(
                config, "control", "notification_url"
            )

            if not ip_address:
                ctrl_config = get_controller_config(
                    get_controller_config_path(config)
                )

                logger.debug(
                    "No 'notification_url' present. Trying to fall back to "
                    "registered IP address."
                )
                ip_address = safe_get(
                    ctrl_config, CONTROLLER_SERVER_SECTION, "address"
                )

    except (IOError, NoSectionError):
        # probably no config file present, so IP cannot be determined.
        pass

    if not ip_address:
        # cannot log this error as we would run into an endless loop
        logger.info("Cannot send notification to CTRL.")
        return

    tree = E("notifyControllerServer",
        E("header",
            E("timestamp", isotime(now())),
            E("instance", get_instance_id(config)),
            E("subsystem", "BROW"),
            E("urgency", urgency)
        ),
        E("body",
            E("summary", summary),
            E("message", message)
        )
    )

    if ip_address.startswith("http://") or ip_address.startswith("https://"):
        pass
    else:
        ip_address = "http://%s" % ip_address

    if not ip_address.endswith("/notify"):
        ip_address += "/notify"

    logger.info("Sending notification to CTRL at IP '%s'." % ip_address)

    req = urllib2.Request(
        url=ip_address,
        data=etree.tostring(tree, pretty_print=True),
        headers={'Content-Type': 'application/xml'}
    )
    try:
        urllib2.urlopen(req, timeout=1)
    except (urllib2.HTTPError, urllib2.URLError), e:
        logger.info("Error sending notification: %s" % e)
        logger.debug(traceback.format_exc() + "\n")


class NotifyControllerServerHandler(logging.Handler):

    def emit(self, record):
        # translate levels to urgency
        if record.levelno > logging.ERROR:
            urgency = "BLOCK"
        elif record.levelno > logging.WARNING:
            urgency = "CRITICAL"
        else:
            urgency = "INFO"

        # start a thread to send the notification
        thread = threading.Thread(
            target=notify, args=(record.message, record.message, urgency)
        )
        thread.daemon = True
        thread.start()
