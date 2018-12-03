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

                logger.debug("Starting query for browses")
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
                    'start_time', 'end_time'
                )
                logger.info("Number browses: %s" % len(browses_qs))

                logger.debug("Starting query for unique times")
                # optimization for when there are a lot of equal time entries
                # like for Sentinel-2
                unique_times_qs = models.Browse.objects.filter(
                    browse_layer=browse_layer_model
                ).values_list(
                    'start_time', 'end_time'
                ).distinct(
                    'start_time', 'end_time'
                ).order_by(
                    'start_time', 'end_time'
                )
                logger.info("Number unique times: %s" % len(unique_times_qs))

                logger.info("Iterating through unique times")
                time_intervals = []
                i = 1
                for unique_time in unique_times_qs:
                    start_time = unique_time[0]
                    end_time = unique_time[1]

                    logger.debug(
                        "Working on unique time %s: %s/%s " %
                        (i, start_time, end_time)
                    )
                    i += 1

                    minx, miny, maxx, maxy = (None,)*4

                    # search for all browses within that time interval and
                    # combine extent
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
                            # change one extent to ]0,360] if difference gets
                            # smaller
                            if minx is not None and maxx is not None:
                                if (minx_tmp <= 0 and maxx_tmp <= 0 and
                                        (minx-maxx_tmp) > (360+minx_tmp-maxx)):
                                    minx_tmp += 360
                                    maxx_tmp += 360
                                elif (minx <= 0 and maxx <= 0 and
                                        (minx_tmp-maxx) > (360+minx-maxx_tmp)):
                                    minx += 360
                                    maxx += 360
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

                    # check if previous element in ordered list overlaps
                    if (
                        len(time_intervals) > 0 and (
                            (
                                (
                                    start_time == end_time or
                                    time_intervals[-1][0] ==
                                    time_intervals[-1][1]
                                ) and (
                                    time_intervals[-1][0] <= end_time and
                                    time_intervals[-1][1] >= start_time
                                )
                            ) or (
                                time_intervals[-1][0] < end_time and
                                time_intervals[-1][1] > start_time
                            )
                        )
                    ):
                        start_time = min(start_time, time_intervals[-1][0])
                        end_time = max(end_time, time_intervals[-1][1])
                        minx = min(minx, time_intervals[-1][2])
                        miny = min(miny, time_intervals[-1][3])
                        maxx = max(maxx, time_intervals[-1][4])
                        maxy = max(maxy, time_intervals[-1][5])
                        time_intervals.pop(-1)
                    time_intervals.append(
                        (start_time, end_time, minx, miny, maxx, maxy)
                    )

                logger.info(
                    "Number non-overlapping time intervals: %s" %
                    len(time_intervals)
                )

                logger.info(
                    "Starting saving time intervals to MapCache SQLite file"
                )
                mapcache_models.Time.objects.bulk_create(
                    [mapcache_models.Time(
                        start_time=time_interval[0],
                        end_time=time_interval[1],
                        minx=time_interval[2],
                        miny=time_interval[3],
                        maxx=time_interval[4],
                        maxy=time_interval[5],
                        source=source
                    ) for time_interval in time_intervals]
                )
                logger.info(
                    "Finished saving time intervals to MapCache SQLite file"
                )

            except Exception as e:
                logger.error(
                    "Failure during generation of MapCache SQLite DB."
                )
                logger.error(
                    "Exception was '%s': %s" % (type(e).__name__, str(e))
                )
                logger.debug(traceback.format_exc() + "\n")
                transaction.rollback(using="mapcache")

            else:
                transaction.commit(using="mapcache")
