#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 European Space Agency
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

from ngeo_browse_server.config.browselayer.decoding import decode_browse_layers
from ngeo_browse_server.config import (
    get_ngeo_config, safe_get, write_ngeo_config, models
)
from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.control.queries import (
    add_browse_layer, update_browse_layer, delete_browse_layer
)
from ngeo_browse_server.filetransaction import FileTransaction
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config
from ngeo_browse_server.namespace import ns_cfg


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--on-error',
            dest='on_error', default="stop",
            choices=["continue", "stop"],
            help=("Declare how errors shall be handled. Possible values are "
                  "'continue' and 'stop'. Default is 'stop'.")
        ),
    )
    
    args = ("<browse-layer-xml-file1> [<browse-layer-xml-file2> ...] ")
    help = ("")


    def handle(self, *filenames, **kwargs):
        System.init()

        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)
        
        logger.info("Starting browse layer configuration from command line.")

        if not filenames:
            raise CommandError("No input files provided.")

        on_error = kwargs["on_error"]

        config = get_ngeo_config()

        no_files_handled_success = 0
        no_files_handled_error = 0
        # handle each file separately
        for filename in filenames:
            try:
                # handle each browse layer xml
                self._handle_file(filename, config)
                no_files_handled_success += 1
            except Exception, e:
                # handle exceptions
                no_files_handled_error += 1
                logger.error("%s: %s" % (type(e).__name__, str(e)))
                if on_error == "continue":
                    # continue the execution with the next file
                    continue
                elif on_error == "stop":
                    # re-raise the exception to stop the execution
                    raise CommandError(e)

        logger.info("Finished browse layer configuration, %d successfully "
                    "handled and %d failed."
                    % (no_files_handled_success, no_files_handled_error))


    @transaction.commit_on_success
    @transaction.commit_on_success(using="mapcache")
    def _handle_file(self, filename, config):
        root = etree.parse(filename)

        start_revision = root.findtext(ns_cfg("startRevision"))
        end_revision = root.findtext(ns_cfg("endRevision"))

        remove_layers_elems = root.xpath("cfg:removeConfiguration/cfg:browseLayers", namespaces={"cfg": ns_cfg.uri})
        add_layers_elems = root.xpath("cfg:addConfiguration/cfg:browseLayers", namespaces={"cfg": ns_cfg.uri})

        add_layers = []
        for layers_elem in add_layers_elems:
            add_layers.extend(decode_browse_layers(layers_elem))

        remove_layers = []
        for layers_elem in remove_layers_elems:
            remove_layers.extend(decode_browse_layers(layers_elem))

        # get the mapcache config xml file path to make it transaction safe
        mapcache_config = get_mapcache_seed_config(config)
        mapcache_xml_filename = mapcache_config["config_file"]

        # transaction safety here
        with FileTransaction((mapcache_xml_filename,), copy=True):
            with transaction.commit_on_success():
                with transaction.commit_on_success(using="mapcache"):
                    for browse_layer in add_layers:
                        if models.BrowseLayer.objects.filter(id=browse_layer.id).exists():
                            update_browse_layer(browse_layer, config)
                        else:
                            add_browse_layer(browse_layer, config)

                    for browse_layer in remove_layers:
                        delete_browse_layer(browse_layer, config=config)

        # set the new revision
        config = config or get_ngeo_config()

        if not config.has_section("config"):
            config.add_section("config")

        revision = int(safe_get(config, "config", "revision", 0))
        config.set("config", "revision", int(end_revision))

        write_ngeo_config()
