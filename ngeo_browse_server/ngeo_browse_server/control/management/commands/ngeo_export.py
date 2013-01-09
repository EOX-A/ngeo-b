import os
import logging
from lxml import etree
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.control.browsereport.parsing import parse_browse_report
from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from eoxserver.core.util.timetools import getDateTime
from ngeo_browse_server.config.models import BrowseReport, BrowseLayer

logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--layer',
            dest='layer',
            help=("Mandatory. The browse layer to be exported.")
        ),
        make_option('--start',
            dest='start',
            help=("The start date and time in ISO 8601 format.")
        ),
        make_option('--end',
            dest='end',
            help=("The end date and time in ISO 8601 format.")
        ),
        make_option('--compression',
            dest='compression', default="gzip",
            choices=["none", "gzip", "bz2"],
            help=("Declare the compression algorithm for the output archive. "
                  "Default is 'gzip'.")
        ),
        make_option('--export-cache', action="store_true",
            dest='export_cache', default=False,
            help=("If this option is set, the tile cache will be exported "
                  "aswell.")
        ),
        make_option('--output',
            dest='output',
            help=("The path for the result archive. Per default, a suitable "
                  "filename will be generated and the file will be stored in "
                  "the current working directory.")
        )
    )
    
    # TODO
    args = ("<browse-report-xml-file1> [<browse-report-xml-file2>] "
            "[--on-error=<on-error>] [--delete-on-success] [--use-store-path | "
            "--path-prefix=<path-to-dir>]")
    help = ("Ingests the specified ngEO Browse Reports. All referenced browse "
            "images are optimized and saved to the configured directory as " 
            "specified in the 'ngeo.conf'. Optionally deletes the original "
            "browse raster files if they were successfully ingested.")

    def handle(self, *args, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)
        
        layer = kwargs.get("layer")
        if not layer:
            raise CommandError("No browse layer was specified.")
        
        start = kwargs.get("start")
        end = kwargs.get("end")
        compression = kwargs.get("compression")
        export_cache = kwargs["export_cache"]
        output = kwargs.get("output")
         
        # parse start/end if given
        if start: 
            start = getDateTime(start)
        if end:
            end = getDateTime(end)
            
        # query the browse layer
        try:
            browse_layer = BrowseLayer.objects.get(id=layer)
        except BrowseLayer.DoesNotExist:
            raise CommandError("Browse layer '%s' does not exist" % layer)
        
        # query browse reports and create XML
        browse_reports = BrowseReport.objects.filter(browse_layer=browse_layer)
        
        # query Browses for the given reports + start/end (if given)
        
        
        
        # - if export cache loop over all browses, create "dim" param and 
        #   retrieve the TileSet
        # - if no output filename is given generate one
        # - create an output package and hand over the params
        
        
        
        
        
        
        
        