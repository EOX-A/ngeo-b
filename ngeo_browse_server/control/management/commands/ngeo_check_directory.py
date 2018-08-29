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
from os import walk
from os.path import isdir, join
import traceback

from django.core.management.base import BaseCommand, CommandError

from ngeo_browse_server.config import models
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    args = ("directory")
    help = ("Checks directory for image files not referenced in DB.")

    def handle(self, *directory, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback_conf = kwargs.get("traceback", False)
        self.set_up_logging(
            ["ngeo_browse_server"], self.verbosity, traceback_conf
        )

        # check consistency
        if not len(directory):
            logger.error("No directory given.")
            raise CommandError("No directory given.")
        elif len(directory) > 1:
            logger.error("Too many directories given.")
            raise CommandError("Too many directories given.")
        else:
            directory = directory[0]
            if not isdir(directory):
                logger.error("No valid directory given.")
                raise CommandError("No valid directory given.")

        logger.info(
            "Starting directory check on '%s' for images files not referenced "
            "in DB." % directory
        )

        self.handle_directory(directory)

        logger.info(
            "Finished directory check on '%s' for image files not referenced "
            "in DB." % directory
        )

    def handle_directory(self, directory):

        try:
            browses_qs = models.Browse.objects.extra(
                select={
                    'file_ref': (
                        '''SELECT lp.path
                        FROM coverages_coveragerecord AS cr,
                             coverages_rectifieddatasetrecord AS rdsr,
                             coverages_localdatapackage AS dp,
                             backends_localpath AS lp
                        WHERE dp.data_location_id = lp.location_ptr_id
                        AND rdsr.data_package_id = dp.datapackage_ptr_id
                        AND cr.resource_ptr_id = rdsr.coveragerecord_ptr_id
                        AND config_browse.coverage_id = cr.coverage_id'''
                    )
                }
            ).values_list(
                'file_ref', flat=True
            ).order_by(
                'file_ref'
            )

            for path, _, files in walk(directory):
                for file in files:
                    if not join(path, file) in browses_qs:
                        logger.info(
                            "'%s' has no reference in DB." % join(path, file)
                        )
                    # else:
                    #     logger.info(
                    #         "'%s' has reference in DB." % join(path, file)
                    #     )

        except Exception as e:
            logger.error(
                "Failure during directory check on '%s' for image files not "
                "referenced in DB." % file
            )
            logger.error(
                "Exception was '%s': %s" % (type(e).__name__, str(e))
            )
            logger.debug(traceback.format_exc() + "\n")
