#------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <https://github.com/EOX-A/ngeo-b>
# Authors: Lubomir Bucek <lubomir.bucek@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

from django.core.management.base import BaseCommand, CommandError
from ngeo_browse_server.config.models import BrowseLayer, Browse

from eoxserver.core.system import System
from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.control.management.commands import LogToConsoleMixIn


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--browse-type',
            dest='browse_type',
            help=("The browses of browse type to be searched.")
        ),
        make_option('--start',
            dest='start',
            help=("The start date and time in ISO 8601 format.")
        ),
        make_option('--end',
            dest='end',
            help=("The end date and time in ISO 8601 format.")
        ),
    )
    args = ("--browse-type=<browse-type> "
            "[--start=<start-date-time>] [--end=<end-date-time>]")
    help = ("For given timestamp and browse type, searches for a continuous array of browses",
      "which overlap in time with given timestamp."
      "The search is a cascade and ends only when a browse is found which"
      "does not intersect in time with the previous/next one."
      "Returns the full time interval start-end.")


    def handle(self, *args, **kwargs):
        System.init()
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        # in case this function is used repeatedly, add logger handle only during first run
        if len([handler for handler in logging.getLogger("ngeo_browse_server").handlers if not isinstance(handler, logging.StreamHandler)]) > 0:
            self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)

        browse_type = kwargs.get("browse_type")
        start = kwargs.get("start")
        end = kwargs.get("end")
        # parse start/end if given
        if start:
            start = getDateTime(start)
        if end:
            end = getDateTime(end)
        logger.info("Starting querying for intersecting time intervals.")
        results = self.handle_query(start, end, browse_type)
        logger.info("Finished querying for intersecting time intervals. Returning result.")
        return results


    def handle_query(self, start, end, browse_type):
        try:
            browse_layer_model = BrowseLayer.objects.get(browse_type=browse_type)
        except BrowseLayer.DoesNotExist:
            logger.error("Browse layer with browse type'%s' does "
                         "not exist" % browse_type)
            raise CommandError("Browse layer with browse type'%s' does "
                               "not exist" % browse_type)
        # get sorted distinct time entries by start_time, end_time
        browses_qs = Browse.objects.all().filter(browse_layer=browse_layer_model
        ).values(
            'start_time', 'end_time'
        ).distinct(
            'start_time', 'end_time'
        ).order_by(
            'start_time', 'end_time'
        )
        new_start = start
        new_end = end
        if len(browses_qs) > 0:
            for i in range(len(browses_qs)):
                # find first intersection
                if browses_qs[i]['start_time'] <= end and browses_qs[i]['end_time'] >= start:
                    # find merged_start_time
                    repeat = True
                    current_index = i  # do not modify for loop iterator
                    while repeat:
                        # search backward until no intersect
                        if current_index > 0:
                            if browses_qs[current_index]['start_time'] <= browses_qs[current_index - 1]['end_time']:
                                # still found intersection, move one left in list
                                current_index -= 1
                            else:
                                # no intersection, save start_time
                                new_start = browses_qs[current_index]['start_time']
                                repeat = False
                        else:
                            # reached start of list
                            new_start = browses_qs[current_index]['start_time']
                            repeat = False
                    # find merged_end_time
                    repeat = True
                    current_index = i
                    while repeat:
                        # search forward until no intersect
                        if current_index < len(browses_qs) - 1:
                            if browses_qs[current_index]['end_time'] >= browses_qs[current_index + 1]['start_time']:
                                # still found intersection, move one right in list
                                current_index += 1
                            else:
                                # no intersection, save end_time
                                new_end = browses_qs[current_index]['end_time']
                                repeat = False
                        else:
                            # reached end of list
                            new_end = browses_qs[current_index]['end_time']
                            repeat = False
                    if repeat is False:
                        break  # go outside of for loop, work done
        else:
            raise CommandError("Browse layer with browse type '%s' is empty" % browse_type)
        results = {
            "merged_start": new_start,
            "merged_end": new_end
        }
        return results