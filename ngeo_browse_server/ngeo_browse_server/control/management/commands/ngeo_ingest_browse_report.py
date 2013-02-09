#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
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


import os
import logging
from lxml import etree
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

from ngeo_browse_server.config.browsereport.parsing import parse_browse_report
from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--on-error',
            dest='on_error', default="stop",
            choices=["continue", "stop"],
            help=("Declare how errors shall be handled. Possible values are "
                  "'continue' and 'stop'. Default is 'stop'.")
        ),
        make_option('--delete-on-success', action="store_true",
            dest='delete_on_success', default=False,
            help=("If this option is set, the original browse files will be "
                  "deleted and only the optimized browse files will be kept.")
        ),
        make_option('--leave-original', action="store_true",
            dest='leave_original', default=False,
            help=("For debugging purposes only. If this option is set, the "
                  "original raster files are not moved from the storage "
                  "directory after a successful/failed ingest.")
        ),
        make_option('--storage-dir',
            dest='storage_dir',
            help=("Use this option to set a path to a custom directory "
                  "entailing the browse raster files to be processed. By "
                  "default, the `storage_dir` option of the ngeo.conf will be "
                  "used.")
        ),
        make_option('--optimized-dir',
            dest='optimized_dir',
            help=("Use this option to set a path to a custom directory "
                  "to store the processed and optimized files. By default, the "
                  "`optimized_files_dir` option of the ngeo.conf will be used.")
        ),
        make_option('--create-result', action="store_true",
            dest='create_result', default=False,
            help=("Use this option to generate an XML ingestion result instead " 
                  "of the usual command line output. The result is printed on "
                  "the standard output stream.")
        )
    )
    
    args = ("<browse-report-xml-file1> [<browse-report-xml-file2>] "
            "[--on-error=<on-error>] [--delete-on-success] [--use-store-path | "
            "--path-prefix=<path-to-dir>]")
    help = ("Ingests the specified ngEO Browse Reports. All referenced browse "
            "images are optimized and saved to the configured directory as " 
            "specified in the 'ngeo.conf'. Optionally deletes the original "
            "browse raster files if they were successfully ingested.")

    def handle(self, *filenames, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)
        
        on_error = kwargs["on_error"]
        delete_on_success = kwargs["delete_on_success"]
        storage_dir = kwargs.get("storage_dir")
        optimized_dir = kwargs.get("optimized_dir")
        create_result = kwargs["create_result"]
        leave_original = kwargs["leave_original"]
        
        # check consistency
        if not len(filenames):
            raise CommandError("No input files given.")
        
        # set config values
        section = "control.ingest"
        config = get_ngeo_config()
        
        # all paths are relative to the current working directory if they are
        # not yet absolute themselves
        if storage_dir is not None:
            storage_dir = os.path.abspath(storage_dir)
            config.set(section, "storage_dir", storage_dir)
            self.print_msg("Using storage directory '%s'." % storage_dir, 2)
            
        if optimized_dir is not None:
            optimized_dir = os.path.abspath(optimized_dir)
            config.set(section, "optimized_files_dir", optimized_dir)
            self.print_msg("Using optimized files directory '%s'."
                           % optimized_dir, 2)
        
        config.set(section, "delete_on_success", delete_on_success)
        config.set(section, "leave_original", leave_original)
        
        # handle each file separately
        for filename in filenames:
            try:
                # handle each browse report
                self._handle_file(filename, create_result, config)
            except Exception, e:
                # handle exceptions
                if on_error == "continue":
                    # just print the traceback and continue
                    self.print_msg("%s: %s" % (type(e).__name__, str(e)),
                                   1, error=True)
                    continue
                
                elif on_error == "stop":
                    # re-raise the exception to stop the execution
                    raise
                


    def _handle_file(self, filename, create_result, config):
        logger.info("Processing input file '%s'." % filename)
        
        # parse the xml file and obtain its data structures as a 
        # parsed browse report.
        self.print_msg("Parsing XML file '%s'." % filename, 1)
        document = etree.parse(filename)
        parsed_browse_report = parse_browse_report(document.getroot())
        
        # ingest the parsed browse report
        self.print_msg("Ingesting browse report with %d browse%s."
                       % (len(parsed_browse_report), 
                          "s" if len(parsed_browse_report) > 1 else ""))
        
        results = ingest_browse_report(parsed_browse_report, config=config)
        
        if create_result:
            # print ingest result
            print(render_to_string("control/ingest_response.xml",
                                   {"results": results}))
        
        self.print_msg("%d browses have been handled whereof %d have been "
                        "successfully replaced and %d successfully inserted."
                        % (results.to_be_replaced, results.actually_replaced,
                            results.actually_inserted))
