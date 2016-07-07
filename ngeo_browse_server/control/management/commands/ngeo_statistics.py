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
from django.db import connection
from django.db.models import Count

from eoxserver.core.util.timetools import getDateTime, isotime

from ngeo_browse_server.config import models
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.mapcache import models as mapcache_models


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
        make_option('--histogram',
            dest='histogram',
            help=("Optional string to specify histogram grouping. Allowed values are 'year', 'month', and 'day'.")
        ),
        make_option('--num-browses', action="store_true",
            dest='num_browses_only', default=False,
            help=("Return only number of available browses.")
        ),
    )

    args = ("browse_layer_id")
    help = ("Provide statistics of the given browse layer.")

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
        histogram = kwargs.get("histogram")
        num_browses_only = kwargs.get("num_browses_only")

        # parse start/end if given
        if start:
            start = getDateTime(start)
        if end:
            end = getDateTime(end)

        if histogram and histogram not in ['year', 'month', 'day']:
            raise CommandError("Wrong value '%s' for histogram given. "
                               "Allowed values are 'year', 'month', and "
                               "'day'." % histogram)
        elif not histogram:
            histogram = 'month'

        # get all browses of browse layer
        browses_qs = models.Browse.objects.filter(
            browse_layer=browse_layer
        )
        times_qs = mapcache_models.Time.objects.filter(
            source=browse_layer.id
        )

        # apply start/end filter
        if start and not end:
            browses_qs = browses_qs.filter(start_time__gte=start)
            times_qs = times_qs.filter(start_time__gte=start)
        elif end and not start:
            browses_qs = browses_qs.filter(end_time__lte=end)
            times_qs = times_qs.filter(end_time__lte=end)
        elif start and end:
            browses_qs = browses_qs.filter(start_time__gte=start,
                                           end_time__lte=end)
            times_qs = times_qs.filter(start_time__gte=start,
                                       end_time__lte=end)

        num_browses = len(browses_qs)
        num_browses_cache = len(times_qs)

        if num_browses_only:
            logger.info("-----------------------------------------------------")
            logger.info("Browse image statistics for browse layer '%s':"
                        % browse_layer.id)
            logger.info("-----------------------------------------------------")
            logger.info("Number of browses: %d" % num_browses)
            logger.info("Number in cache:   %d" % num_browses_cache)
            logger.info("-----------------------------------------------------")
        #TODO: Add further statistics switches
        #elif:
        else:
            logger.info("-----------------------------------------------------")
            logger.info("Full statistics for browse layer '%s':"
                        % browse_layer.id)
            logger.info("-----------------------------------------------------")
            logger.info("Number of browses: %d" % num_browses)
            logger.info("Number in cache:   %d" % num_browses_cache)
            logger.info("-----------------------------------------------------")
            logger.info("Time histogram: ")
            truncate_date = connection.ops.date_trunc_sql(histogram, 'start_time')
            browses_qs_hist = browses_qs.extra({'date':truncate_date}).values('date').annotate(no_entries=Count('browse_identifier')).order_by('date')
            for hist_entry in browses_qs_hist:
                logger.info("%s: %d" % (hist_entry["date"].strftime("%Y-%m-%d" if histogram=="day" else "%Y" if histogram=="year" else "%Y-%m"), hist_entry["no_entries"]))
            logger.info("-----------------------------------------------------")
