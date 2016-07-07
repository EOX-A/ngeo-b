#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from eoxserver.core.util.timetools import getDateTime, isotime

from ngeo_browse_server.config import models
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.mapcache.tasks import seed_mapcache
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--start',
            dest='start',
            help=("Optional start date and time in ISO 8601 format.")
        ),
        make_option('--end',
            dest='end',
            help=("Optional end date and time in ISO 8601 format.")
        ),
        make_option('--dry-run', action="store_true",
            dest='dry_run', default=False,
            help=("Optional switch to only print times without actually "
                  "(re)seeding.")
        ),
        make_option('--force', action="store_true",
            dest='force', default=False,
            help=("Optional switch to force tile recreation.")
        ),
    )

    args = ("browse_layer_id")
    help = ("Seeds or reseeds the cache of the given browse layer.")

    def handle(self, *browse_layer_id, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)

        # check consistency
        if not len(browse_layer_id):
            logger.error("No browse layer given.")
            raise CommandError("No browse layer given.")
        elif len(browse_layer_id) > 1:
            logger.error("Too many browse layers given.")
            raise CommandError("Too many browse layers given.")
        else:
            browse_layer_id = browse_layer_id[0]

        try:
            # get the according browse layer
            browse_layer = models.BrowseLayer.objects.get(id=browse_layer_id)
        except models.BrowseLayer.DoesNotExist:
            logger.error("Browse layer '%s' does not exist."
                         % browse_layer_id)
            raise CommandError("Browse layer '%s' does not exist."
                               % browse_layer_id)

        start = kwargs.get("start")
        end = kwargs.get("end")
        dry_run = kwargs.get("dry_run")
        force = kwargs.get("force")

        # parse start/end if given
        if start:
            start = getDateTime(start)
        if end:
            end = getDateTime(end)

        if force:
            logger.info("Starting reseeding browse layer '%s'." % browse_layer_id)
        else:
            logger.info("Starting seeding browse layer '%s'." % browse_layer_id)

        times_qs = mapcache_models.Time.objects.filter(
            source=browse_layer.id
        )

        # apply start/end filter
        if start and not end:
            times_qs = times_qs.filter(start_time__gte=start)
        elif end and not start:
            times_qs = times_qs.filter(end_time__lte=end)
        elif start and end:
            times_qs = times_qs.filter(start_time__gte=start,
                                       end_time__lte=end)

        for time_model in times_qs:

            if dry_run:
                logger.info("Time span to (re)seed is %s/%s."
                            % (isotime(time_model.start_time),
                               isotime(time_model.end_time)))
            else:
                try:
                    logger.info("(Re)seeding time span %s/%s."
                                % (isotime(time_model.start_time),
                                   isotime(time_model.end_time)))
                    seed_mapcache(tileset=browse_layer.id,
                                  grid=browse_layer.grid,
                                  minx=time_model.minx, miny=time_model.miny,
                                  maxx=time_model.maxx, maxy=time_model.maxy,
                                  minzoom=browse_layer.lowest_map_level,
                                  maxzoom=browse_layer.highest_map_level,
                                  start_time=time_model.start_time,
                                  end_time=time_model.end_time,
                                  delete=False, force=force,
                                  **get_mapcache_seed_config())
                    logger.info("Successfully finished (re)seeding time span.")
                except Exception, e:
                    logger.warn("(Re)seeding failed: %s" % str(e))

        if force:
            logger.info("Finished reseeding of browse layer '%s'."
                        % browse_layer_id)
        else:
            logger.info("Finished seeding of browse layer '%s'."
                        % browse_layer_id)
