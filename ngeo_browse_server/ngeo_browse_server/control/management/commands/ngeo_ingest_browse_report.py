import os
import logging
from lxml import etree
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.template.loader import render_to_string
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

from ngeo_browse_server.control.ingest import (
    ingest_browse_report, get_storage_path
)
from ngeo_browse_server.control.ingest.parsing import parse_browse_report


logger = logging.getLogger(__name__)

class Command(CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--on-error',
            dest='on_error', default="rollback",
            choices=["continue", "stop", "rollback"],
            help="Declare how errors shall be handled. Default is 'rollback'."
        ),
        make_option('--delete-original', action="store_true",
            dest='delete_original', default=False,
            help=("If this option is set, the original browse files will be "
                  "deleted and only the optimized browse files will be kept.")
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
            "[--on-error=<on-error>] [--delete-original] [--use-store-path | "
            "--path-prefix=<path-to-dir>]")
    help = ("Ingests the specified ngEO Browse Reports. All referenced browse "
            "images are optimized and saved to the configured directory as " 
            "specified in the 'ngeo.conf'. Optionally deletes the original "
            "browse raster files.")

    def handle(self, *filenames, **kwargs):
        # parse command arguments
        self.verbosity = kwargs.get("v", 1)
        
        on_error = kwargs["on_error"]
        delete_original = kwargs["delete_original"]
        storage_dir = kwargs.get("storage_dir")
        optimized_dir = kwargs.get("optimized_dir")
        create_result = kwargs["create_result"]
        
        # check consistency
        if not len(filenames):
            raise CommandError("No input files given.")
        
        with transaction.commit_manually():
            for filename in filenames:
                sid = transaction.savepoint()
                try:
                    # handle each browse report
                    self._handle_file(filename, storage_dir, optimized_dir,
                                      delete_original, create_result)
                except Exception, e:
                    # handle exceptions
                    if on_error == "continue":
                        self.print_msg("%s: %s" % (type(e).__name__, str(e)),
                                       1, error=True)
                        # just rollback to the last savepoint and continue
                        transaction.savepoint_rollback(sid)
                    elif on_error == "stop":
                        # rollback to the last savepoint, commit the transaction
                        # and stop here
                        # TODO: 
                        transaction.savepoint_rollback(sid)
                        transaction.commit()
                        raise
                    elif on_error == "rollback":
                        # rollback the complete transaction and stop
                        transaction.rollback()
                        raise
                
                transaction.savepoint_commit(sid)
            
            transaction.commit()


    def _handle_file(self, filename, storage_dir, optimized_dir,
                     delete_original, create_result):
        logger.info("Processing input file '%s'." % filename)
        
        # parse the xml file and obtain its data structures as a 
        # parsed browse report.
        self.print_msg("Parsing XML file '%s'." % filename, 1)
        document = etree.parse(filename)
        parsed_browse_report = parse_browse_report(document.getroot())
        
        # ingest the parsed browse report
        self.print_msg("Ingesting browse report with %d browses.", 1)
        
        if not create_result:
            result = ingest_browse_report(parsed_browse_report,
                                          storage_dir=storage_dir,
                                          optimized_dir=optimized_dir,
                                          reraise_exceptions=True)
            
            self.print_msg("%d browses have been successfully ingested. %d "
                           "replaced, %d inserted."
                           % (result.to_be_replaced, result.actually_replaced,
                              result.actually_inserted), 1)    
            
        else:
            result = ingest_browse_report(parsed_browse_report,
                                          storage_dir=storage_dir,
                                          optimized_dir=optimized_dir,
                                          reraise_exceptions=False)
            
            # print ingest result
            print(render_to_string("control/ingest_response.xml",
                                   {"result": result}))
        
        
        # if requested delete the original raster files.
        if delete_original:
            for parsed_browse in parsed_browse_report:
                original_filename = get_storage_path(parsed_browse.file_name,
                                                     storage_dir)
                
                logger.info("Removing original raster file '%s'."
                            % original_filename)
                self.print_msg("Removing original raster file '%s'."
                               % original_filename, 1)
                os.remove(original_filename)
