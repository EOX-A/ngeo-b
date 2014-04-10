#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
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
import logging
from lxml import etree
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.db import transaction
from eoxserver.core.system import System
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.config.browselayer.decoding import decode_browse_layers
from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.control.control.reporting import (
    send_report, save_report
)


logger = logging.getLogger(__name__)

class Command(LogToConsoleMixIn, CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--begin', 
            dest='begin', default=None,
            help=("")
        ),
        make_option('--end', 
            dest='end', default=None,
            help=("")
        ),
        make_option('--url', 
            dest="url", default=None,
            help=("")
        ),
        make_option('--filename', 
            dest="filename",
            help=("")
        ),
        make_option('--method',
            dest="method", default="save",
            help=("save/send the report")
        )
    )
    
    args = ("")
    help = ("")

    def handle(self, begin=None, end=None, url=None, filename=None, method=None, **kwargs):

        if begin:
            begin = getDateTime(begin)

        if end: 
            end = getDateTime(end)

        if method == "save":
            save_report(filename, begin, end)
        elif method == "send":
            send_report(url, begin, end)
        else:
            raise CommandError("Invalid method '%s'" % method)
