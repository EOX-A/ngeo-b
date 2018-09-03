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
from os.path import isfile, exists
import traceback

from django.core.management.base import BaseCommand, CommandError

from ngeo_browse_server.config import models
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    args = ("filelist_in", "filelist_out_nodb", "filelist_out_nofs")
    help = ("Checks list of files for image files not referenced in DB.")

    def handle(self, *filelists, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback_conf = kwargs.get("traceback", False)
        self.set_up_logging(
            ["ngeo_browse_server"], self.verbosity, traceback_conf
        )

        # check consistency
        if not len(filelists):
            logger.error("No filelists given.")
            raise CommandError("No filelists given.")
        elif len(filelists) > 3:
            logger.error("Too many filelists given.")
            raise CommandError("Too many filelists given.")
        elif len(filelists) < 3:
            logger.error("Need three filelists.")
            raise CommandError("Need three filelists.")
        else:
            filelist_in = filelists[0]
            filelist_out_nodb = filelists[1]
            filelist_out_nofs = filelists[2]
            if not isfile(filelist_in):
                logger.error("filelist_in '%s' is not a file." % filelist_in)
                raise CommandError(
                    "filelist_in '%s' is not a file." % filelist_in
                )
            if exists(filelist_out_nodb) or exists(filelist_out_nofs):
                logger.error(
                    "One of out filelists '%s' and '%s' exists."
                    % (filelist_out_nodb, filelist_out_nofs)
                )
                raise CommandError(
                    "One of out filelists '%s' and '%s' exists."
                    % (filelist_out_nodb, filelist_out_nofs)
                )

        logger.info(
            "Starting list of files check on '%s' for images files not "
            "referenced in DB." % filelist_in
        )

        self.handle_filelist(filelist_in, filelist_out_nodb, filelist_out_nofs)

        logger.info(
            "Finished list of files check on '%s' for image files not "
            "referenced in DB." % filelist_in
        )

    def handle_filelist(
        self, filelist_in, filelist_out_nodb, filelist_out_nofs
    ):

        try:
            filenames_db = set(models.Browse.objects.extra(
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
            ))

            filenames_in = set(line.strip() for line in open(filelist_in))

            filenames_nodb = filenames_in - filenames_db
            logger.info("Found %s not referenced files." % len(filenames_nodb))

            filenames_nofs = filenames_db - filenames_in
            logger.info(
                "Found %s DB entries not in the filelist. Please use this "
                "info with caution, these entries may have been ingested "
                "since the generation of the filelist."
                % len(filenames_nofs)
            )

            with open(filelist_out_nodb, "w") as f:
                f.writelines("%s\n" % line for line in filenames_nodb)

            with open(filelist_out_nofs, "w") as f:
                f.writelines("%s\n" % line for line in filenames_nofs)

        except Exception as e:
            logger.error(
                "Failure during filelist check on '%s' for image files not "
                "referenced in DB." % filelist_in
            )
            logger.error(
                "Exception was '%s': %s" % (type(e).__name__, str(e))
            )
            logger.debug(traceback.format_exc() + "\n")
