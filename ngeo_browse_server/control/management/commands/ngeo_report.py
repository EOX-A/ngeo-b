#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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


from os.path import join, basename
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.config import get_ngeo_config, safe_get
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.control.control.reporting import (
    send_report, save_report
)


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--begin',
            dest='begin', default=None,
            help=("")
        ),
        make_option('--end',
            dest='end', default=None,
            help=("")
        ),
        make_option('--access-logfile',
            dest="access_logfile",
            help=("")
        ),
        make_option('--report-logfile',
            dest="report_logfile",
            help=("")
        ),
        make_option('--url',
            dest="url", default=None,
            help=("")
        ),
        make_option('--filename',
            dest="filename",
            help=("")
        )
    )

    args = ("")
    help = ("")

    def handle(self, begin=None, end=None, url=None, filename=None,
               access_logfile=None, report_logfile=None, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)

        conf = get_ngeo_config()

        report_store_dir = safe_get(
            conf, "control", "report_store_dir", "/var/www/ngeo/store/reports/"
        )

        filename = join(report_store_dir, basename(filename))

        logger.info("Starting report generation from command line.")

        if begin:
            begin = getDateTime(begin)

        if end:
            end = getDateTime(end)

        if filename and url:
            logger.error("Both Filename and URL specified.")
            raise CommandError("Both Filename and URL specified.")

        if filename:
            logger.info("Save report to file '%s'." % filename)
            save_report(filename, begin, end, access_logfile, report_logfile)
        elif url:
            logger.info("Send report to URL '%s'." % url)
            send_report(url, begin, end, access_logfile, report_logfile)
        else:
            logger.error("Neither Filename nor URL specified.")
            raise CommandError("Neither Filename nor URL specified.")

        logger.info("Successfully finished report generation.")
