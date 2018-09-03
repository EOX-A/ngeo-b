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
from os.path import isfile
import traceback

from django.core.management.base import BaseCommand

from eoxserver.core.system import System

from ngeo_browse_server.config import models
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.control.queries import remove_browse


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--delete', action="store_true",
            dest='delete', default=False,
            help=("Optional switch to delete browses with dangling references"
                  " to files.")
        ),
    )

    help = ("Checks DB for dangling references to files.")

    def handle(self, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback_conf = kwargs.get("traceback", False)
        self.set_up_logging(
            ["ngeo_browse_server"], self.verbosity, traceback_conf
        )

        logger.info("Starting DB check for dangling references to files.")

        delete = kwargs.get("delete")
        if delete:
            System.init()
            logger.info("Caution, deletion enabled.")

        for browse_layer_model in models.BrowseLayer.objects.all():
            self.handle_browse_layer(browse_layer_model, delete)

        logger.info("Finished DB check for dangling references to files.")

    def handle_browse_layer(self, browse_layer_model, delete=False):

        try:
            logger.info("Checking layer '%s'" % browse_layer_model.id)

            browses_qs = models.Browse.objects.filter(
                browse_layer=browse_layer_model
            ).extra(
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
                'coverage_id', 'file_ref'
            )

            counter = 1

            # iterate through browses
            for browse in browses_qs:
                coverage_id = browse[0]
                file_ref = browse[1]

                if not(isfile(file_ref)):
                    if delete:
                        logger.info(
                            "%s: Deleting '%s' with dangling reference to "
                            "'%s'."
                            % (counter, coverage_id, file_ref)
                        )
                        browse_model = models.Browse.objects.get(
                            browse_layer=browse_layer_model,
                            coverage_id=coverage_id
                        )
                        _, _ = remove_browse(
                            browse_model, browse_layer_model,
                            coverage_id, []
                        )
                    else:
                        logger.info(
                            "%s: '%s' has dangling reference to '%s'."
                            % (counter, coverage_id, file_ref)
                        )
                else:
                    logger.info(
                        "%s: '%s' has good reference to '%s'."
                        % (counter, coverage_id, file_ref)
                    )

                counter += 1

        except Exception as e:
            logger.error(
                "Failure during DB check for dangling references to files."
            )
            logger.error(
                "Exception was '%s': %s" % (type(e).__name__, str(e))
            )
            logger.debug(traceback.format_exc() + "\n")
