#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 European Space Agency
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

from os.path import exists
from os import remove
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from eoxserver.core.system import System

from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.control.queries import delete_browse_layer
from ngeo_browse_server.config.models import BrowseLayer, Browse


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--layer', '--browse-layer',
            dest='browse_layer_id',
            help=("The identifier of the layer to be purged.")
        ),
        make_option('--browse-type',
            dest='browse_type',
            help=("The browse type of the layer to be purged.")
        )
    )

    args = ("--layer=<layer-id> | --browse-type=<browse-type> ")
    help = ("Completely purges a browse layer identified by '--layer' or "
            "'--browse-type'. Purge removes everything related to the layer: "
            "the layer itself, all browses, the mapcache configuration and "
            "the cache.")

    def handle(self, *args, **kwargs):
        System.init()

        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)

        logger.info("Starting browse layer purging from command line.")

        browse_layer_id = kwargs.get("browse_layer_id")
        browse_type = kwargs.get("browse_type")
        if not browse_layer_id and not browse_type:
            logger.error("No browse layer or browse type was specified.")
            raise CommandError("No browse layer or browse type was specified.")
        elif browse_layer_id and browse_type:
            logger.error("Both browse layer and browse type were specified.")
            raise CommandError(
                "Both browse layer and browse type were specified."
            )

        self._handle(browse_layer_id, browse_type)
        logger.info("Successfully finished browse layer purging from command line.")

    def _handle(self, browse_layer_id, browse_type):
        from ngeo_browse_server.control.queries import remove_browse

        # query the browse layer
        if browse_layer_id:
            try:
                browse_layer_model = BrowseLayer.objects.get(id=browse_layer_id)
            except BrowseLayer.DoesNotExist:
                logger.error(
                    "Browse layer '%s' does not exist" % browse_layer_id
                )
                raise CommandError(
                    "Browse layer '%s' does not exist" % browse_layer_id
                )
        else:
            try:
                browse_layer_model = BrowseLayer.objects.get(
                    browse_type=browse_type
                )
            except BrowseLayer.DoesNotExist:
                logger.error("Browse layer with browse type '%s' does "
                             "not exist" % browse_type)
                raise CommandError("Browse layer with browse type '%s' does "
                                   "not exist" % browse_type)

        # get all browses of browse layer
        browses_qs = Browse.objects.all().filter(browse_layer=browse_layer_model)

        paths_to_delete = []
        seed_areas = []

        with transaction.commit_on_success():
            with transaction.commit_on_success(using="mapcache"):
                logger.info("Deleting '%d' browse%s from database."
                            % (browses_qs.count(),
                               "s" if browses_qs.count() > 1 else ""))
                # go through all browses to be deleted
                for browse_model in browses_qs:
                    _, filename = remove_browse(
                        browse_model, browse_layer_model,
                        browse_model.coverage_id, seed_areas,
                        unseed=False
                    )

                    paths_to_delete.append(filename)

        # loop through optimized browse images and delete them
        # This is done at this point to make sure a rollback is possible
        # if there is an error while deleting the browses and coverages
        for file_path in paths_to_delete:
            if exists(file_path):
                remove(file_path)
                logger.info("Optimized browse image deleted: %s" % file_path)
            else:
                logger.warning("Optimized browse image to be deleted not found "
                               "in path: %s" % file_path)

        delete_browse_layer(browse_layer_model, purge=True)
