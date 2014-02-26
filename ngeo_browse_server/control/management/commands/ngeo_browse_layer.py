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

from ngeo_browse_server.config.browselayer.decoding import decode_browse_layers
from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.control.queries import (
    add_browse_layer, update_browse_layer, delete_browse_layer
)

logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--add',
            action="store_const", const="add", dest='mode', default="add",
            help=("")
        ),
        make_option('--update',
            action="store_const", const="update", dest='mode',
            help=("")
        ),
        make_option('--remove',
            action="store_const", const="remove", dest='mode',
            help=("")
        ),
        make_option('--on-error',
            dest='on_error', default="stop",
            choices=["continue", "stop"],
            help=("Declare how errors shall be handled. Possible values are "
                  "'continue' and 'stop'. Default is 'stop'.")
        ),
    )
    
    args = ("--add | --update | --remove "
            "<browse-layer-xml-file1> [<browse-layer-xml-file2> ...] ")
    help = ("")

    def handle(self, *filenames, **kwargs):

        System.init()

        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)
        
        mode = kwargs["mode"]
        on_error = kwargs["on_error"]

        config = get_ngeo_config()

        if not filenames:
            raise CommandError("No input files provided.")

        # handle each file separately
        for filename in filenames:
            try:
                # handle each browse report
                self._handle_file(filename, mode, config)
            except Exception, e:
                # handle exceptions
                if on_error == "continue":
                    # just print the traceback and continue
                    self.print_msg("%s: %s" % (type(e).__name__, str(e)),
                                   1, error=True)
                    continue
                
                elif on_error == "stop":
                    # re-raise the exception to stop the execution
                    raise


    @transaction.commit_on_success
    @transaction.commit_on_success(using="mapcache")
    def _handle_file(self, filename, mode, config):
        browse_layers = decode_browse_layers(etree.parse(filename))

        for browse_layer in browse_layers:
            if mode == "add":
                add_browse_layer(browse_layer, config)

            elif mode == "update":
                update_browse_layer(browse_layer, config)

            elif mode == "remove":
                delete_browse_layer(browse_layer, config)

