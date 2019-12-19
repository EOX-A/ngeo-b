#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Daniel Santillan <daniel.santillan@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

from os.path import exists
from os import remove
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from eoxserver.core.system import System
from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.config.models import BrowseLayer, Browse
from ngeo_browse_server.mapcache.tasks import seed_mapcache
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config


logger = logging.getLogger(__name__)


def getCoverageIds(option, opt, value, parser):
    """
    Splits command line argument which should be a list separated by comma.
    """
    setattr(parser.values, option.dest, value.split(','))


class Command(LogToConsoleMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--layer', '--browse-layer',
            dest='browse_layer_id',
            help=("The browse layer to be deleted.")
        ),
        make_option(
            '--browse-type',
            dest='browse_type',
            help=("The browses of browse type to be deleted.")
        ),
        make_option(
            '--start',
            dest='start',
            help=("The start date and time in ISO 8601 format.")
        ),
        make_option(
            '--end',
            dest='end',
            help=("The end date and time in ISO 8601 format.")
        ),
        make_option('--id',
            dest='coverage_id',
            type="string",
            help=("String coverage_id of browse to be deleted or list of strings separated by comma. Usually created as browse_layer_id + _ + browse_identifier"),
            action="callback",
            callback=getCoverageIds
        ),
        make_option('--summary',
            dest='return_summary',
            action="store_true",
            help=("If option is used, a summary results object will be returned.")
        )
    )

    args = ("--layer=<layer-id> | --browse-type=<browse-type> "
            "[--start=<start-date-time>] [--end=<end-date-time>]"
            "[--id=<coverage-identifier>]"
            "[--summary=<return-summary>]")
    help = ("Deletes the browses specified by either the layer ID, "
            "its browse type. Optionally also by browse_identifier "
            "or start and or end time."
            "Only browses that are completely contained in the time interval"
            "are actually deleted.")

    def handle(self, *args, **kwargs):
        System.init()

        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)

        # in case this function is used repeatedly, add logger handle only during first run
        if len([handler for handler in logging.getLogger("ngeo_browse_server").handlers if not isinstance(handler, logging.StreamHandler)]) > 0:
            self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)

        logger.info("Starting browse deletion from command line.")

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

        start = kwargs.get("start")
        end = kwargs.get("end")
        coverage_id = kwargs.get("coverage_id")
        return_summary = kwargs.get("return_summary")
        # parse start/end if given
        if start:
            start = getDateTime(start)
        if end:
            end = getDateTime(end)

        summary = self._handle(start, end, coverage_id, browse_layer_id, browse_type)
        logger.info("Successfully finished browse deletion from command line.")
        if return_summary:
            return summary


    def _handle(self, start, end, coverage_id, browse_layer_id, browse_type):
        from ngeo_browse_server.control.queries import remove_browse
        summary = {
          "browses_found": 0,
          "files_deleted": 0,
          "deleted": {},
        }
        # query the browse layer
        if browse_layer_id:
            try:
                browse_layer_model = BrowseLayer.objects.get(
                    id=browse_layer_id
                )
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
                logger.error("Browse layer with browse type'%s' does "
                             "not exist" % browse_type)
                raise CommandError("Browse layer with browse type'%s' does "
                                   "not exist" % browse_type)

        # get all browses of browse layer
        browses_qs = Browse.objects.all().filter(browse_layer=browse_layer_model)

        # apply coverage_id filter for string or list of strings
        # then time filter should not be applicable
        if isinstance(coverage_id, list):
            browses_qs = browses_qs.filter(coverage_id__in=coverage_id)
        elif isinstance(coverage_id, (str, unicode)):
            browses_qs = browses_qs.filter(coverage_id=coverage_id)
        else:
            # apply start/end filter
            if start and not end:
                browses_qs = browses_qs.filter(start_time__gte=start)
            elif end and not start:
                browses_qs = browses_qs.filter(end_time__lte=end)
            elif start and end:
                browses_qs = browses_qs.filter(start_time__gte=start, end_time__lte=end)

        paths_to_delete = []
        seed_areas = []
        deleted = {}
        summary["browses_found"] = browses_qs.count()

        with transaction.commit_on_success():
            with transaction.commit_on_success(using="mapcache"):
                logger.info("Deleting '%d' browse%s from database."
                            % (browses_qs.count(),
                               "s" if browses_qs.count() > 1 else ""))
                # go through all browses to be deleted
                for browse_model in browses_qs:
                    # reference to ID is lost after remove_browse completes
                    save_id = browse_model.coverage_id
                    _, filename = remove_browse(browse_model, browse_layer_model, browse_model.coverage_id, seed_areas)
                    paths_to_delete.append(filename)
                    deleted[save_id] = {
                        "start": browse_model.start_time,
                        "end": browse_model.end_time,
                    }
        # loop through optimized browse images and delete them
        # This is done at this point to make sure a rollback is possible
        # if there is an error while deleting the browses and coverages
        for file_path in paths_to_delete:
            if exists(file_path):
                remove(file_path)
                summary["files_deleted"] += 1
                logger.info("Optimized browse image deleted: %s" % file_path)
            else:
                logger.warning("Optimized browse image to be deleted not found "
                               "in path: %s" % file_path)

        # only if either start or end is present browses are left
        if start or end or coverage_id:
            if start:
                if end:
                    seed_areas = [
                        area for area in seed_areas
                        if not (area[4] >= start and area[5] <= end)
                    ]
                else:
                    seed_areas = [
                        area for area in seed_areas if not (area[4] >= start)
                    ]
            elif end:
                seed_areas = [
                    area for area in seed_areas if not (area[5] <= end)
                ]

            for minx, miny, maxx, maxy, start_time, end_time in seed_areas:
                try:

                    # seed MapCache synchronously
                    # TODO: maybe replace this with an async solution
                    seed_mapcache(tileset=browse_layer_model.id,
                                  grid=browse_layer_model.grid,
                                  minx=minx, miny=miny,
                                  maxx=maxx, maxy=maxy,
                                  minzoom=browse_layer_model.lowest_map_level,
                                  maxzoom=browse_layer_model.highest_map_level,
                                  start_time=start_time,
                                  end_time=end_time,
                                  delete=False,
                                  **get_mapcache_seed_config())
                    logger.info("Successfully finished seeding.")

                except Exception, e:
                    logger.warn("Seeding failed: %s" % str(e))

        summary["deleted"] = deleted
        return summary
        # TODO:
        #   - think about what to do with brows report
        #   - think about what to do with cache
