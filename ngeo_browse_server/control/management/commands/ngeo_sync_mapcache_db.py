#------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#------------------------------------------------------------------------------

import logging
from optparse import make_option
from os.path import abspath, exists
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction
from django.db.models import F, Q

from eoxserver.core.system import System

from ngeo_browse_server.config import models
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.mapcache import models as mapcache_models


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--force', action="store_true",
            dest='force', default=False,
            help=("Optional switch to alter existing file.")
        ),
    )

    help = ("Synchronizes the MapCache SQLite DB holding times and extents.")

    def handle(self, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback_conf = kwargs.get("traceback", False)
        self.set_up_logging(
            ["ngeo_browse_server"], self.verbosity, traceback_conf
        )

        logger.info("Starting synchronization of MapCache SQLite DB holding "
                    "times and extents.")

        force = kwargs.get("force")
        if force:
            # TODO
            logger.error("Changing existing SQLite file is not implemented.")
            raise CommandError(
                "Changing existing SQLite file is not implemented."
            )
        else:
            db_path = abspath(settings.DATABASES["mapcache"]["NAME"])
            if exists(db_path):
                logger.error("MapCache SQLite exists exiting.")
                raise CommandError("MapCache SQLite exists exiting.")

        call_command("syncdb", database="mapcache", interactive=False)

        System.init()

        for browse_layer_model in models.BrowseLayer.objects.all():
            self.handle_browse_layer(browse_layer_model)

        logger.info("Finished generation of MapCache SQLite DB holding times "
                    "and extents.")

    def handle_browse_layer(self, browse_layer_model):

        with transaction.commit_manually(using="mapcache"):
            try:
                logger.info("Syncing layer '%s'" % browse_layer_model.id)

                source, _ = mapcache_models.Source.objects.get_or_create(
                    name=browse_layer_model.id)

                browses_qs = models.Browse.objects.filter(
                    browse_layer=browse_layer_model
                ).extra(
                    select={
                        # ugly, ugly hack to get the extent from a browse by
                        # manually joining the ExtentRecord model of the
                        # associated coverage as only a single value is
                        # allowed in a subquery, the values are encoded in a
                        #string and joined by ','
                        'extent': (
                            '''SELECT extent.minx || ',' || extent.miny || ','
                                      || extent.maxx || ',' || extent.maxy
                            FROM coverages_extentrecord AS extent,
                                 coverages_rectifieddatasetrecord AS
                                 rectifieddataset,
                                 coverages_coveragerecord AS coverage
                            WHERE rectifieddataset.extent_id = extent.id
                            AND rectifieddataset.coveragerecord_ptr_id =
                                coverage.resource_ptr_id
                            AND config_browse.coverage_id =
                                coverage.coverage_id'''
                        )
                    }
                ).values(
                    'start_time', 'end_time', 'extent'
                ).order_by(
                    'start_time'
                )
                logger.info("Number browses: %s" % len(browses_qs))

                unique_times_qs = models.Browse.objects.filter(
                    browse_layer=browse_layer_model
                ).values(
                    'start_time', 'end_time'
                ).distinct(
                    'start_time', 'end_time'
                ).order_by(
                    'start_time'
                )
                logger.info("Number unique times: %s" % len(unique_times_qs))

                # iterate through unique times
                for unique_time in unique_times_qs:

                    start_time = unique_time['start_time']
                    end_time = unique_time['end_time']
                    minx, miny, maxx, maxy = (None,)*4

                    # search for all browses with that time and combine extent
                    time_qs = browses_qs.filter(
                        start_time=start_time,
                        end_time=end_time
                    )

                    if len(time_qs) <= 0:
                        logger.errro(
                            "DB queries got different results which should "
                            "never happen."
                        )
                        raise CommandError("DB queries got different results.")
                    else:
                        for time in time_qs:
                            # decode extent from the above hack
                            minx_tmp, miny_tmp, maxx_tmp, maxy_tmp = (
                                float(v) for v in time['extent'].split(',')
                            )
                            minx = min(
                                i for i in [minx_tmp, minx] if i is not None
                            )
                            miny = min(
                                i for i in [miny_tmp, miny] if i is not None
                            )
                            maxx = max(
                                i for i in [maxx_tmp, maxx] if i is not None
                            )
                            maxy = max(
                                i for i in [maxy_tmp, maxy] if i is not None
                            )

                    #TODO guess it would be faster to first compute all Time
                    #models and save all at once?

                    # search for time entries with an overlapping time span
                    if start_time == end_time:
                        times_qs = mapcache_models.Time.objects.filter(
                            source=source,
                            start_time__lte=end_time,
                            end_time__gte=start_time
                        )
                    else:
                        times_qs = mapcache_models.Time.objects.filter(
                            Q(source=source),
                            Q(start_time__lt=end_time,
                              end_time__gt=start_time) |
                            Q(start_time=F("end_time"),
                              start_time__lte=end_time,
                              end_time__gte=start_time)
                        )

                    if len(times_qs) > 0:
                        # If there are overlapping time entries, merge them
                        for time_model in times_qs:
                            minx = min(minx, time_model.minx)
                            miny = min(miny, time_model.miny)
                            maxx = max(maxx, time_model.maxx)
                            maxy = max(maxy, time_model.maxy)
                            start_time = min(start_time, time_model.start_time)
                            end_time = max(end_time, time_model.end_time)

                        times_qs.delete()

                    time_model = mapcache_models.Time(
                        start_time=start_time, end_time=end_time, minx=minx,
                        miny=miny, maxx=maxx, maxy=maxy, source=source
                    )

                    time_model.full_clean()
                    time_model.save()

                transaction.commit(using="mapcache")

            except Exception as e:
                logger.error(
                    "Failure during generation of MapCache SQLite DB."
                )
                logger.error(
                    "Exception was '%s': %s" % (type(e).__name__, str(e))
                )
                logger.debug(traceback.format_exc() + "\n")
                transaction.rollback(using="mapcache")
