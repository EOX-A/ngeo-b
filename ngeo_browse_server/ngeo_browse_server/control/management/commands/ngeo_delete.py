#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Daniel Santillan <daniel.santillan@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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



from os.path import basename
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models.aggregates import Count
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.core.system import System
from eoxserver.core.util.timetools import getDateTime, isotime

from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.config.models import ( 
    BrowseReport, BrowseLayer, Browse
)
from ngeo_browse_server.control.browsereport import data as browsereport_data
from ngeo_browse_server.control.browsereport.serialization import serialize_browse_report
from ngeo_browse_server.control.browselayer import data as browselayer_data
from ngeo_browse_server.control.browselayer.serialization import serialize_browse_layers
from ngeo_browse_server.control.migration import package
from ngeo_browse_server.mapcache import tileset
from ngeo_browse_server.mapcache.config import get_tileset_path
from ngeo_browse_server.mapcache.tileset import URN_TO_GRID


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--layer', '--browse-layer',
            dest='browse_layer_id',
            help=("The browse layer to be exported.")
        ),
        make_option('--browse-type',
            dest='browse_type',
            help=("The browse type to be exported.")
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
            choices=["none", "gzip", "gz", "bzip2", "bz2"],
            help=("Declare the compression algorithm for the output package. "
                  "Default is 'gzip'.")
        ),
        make_option('--export-cache', action="store_true",
            dest='export_cache', default=False,
            help=("If this option is set, the tile cache will be exported "
                  "aswell.")
        ),
        make_option('--output', '--output-path',
            dest='output_path',
            help=("The path for the result package. Per default, a suitable "
                  "filename will be generated and the file will be stored in "
                  "the current working directory.")
        )
    )
    
    args = ("--layer=<layer-id> | --browse-type=<browse-type> "
            "[--start=<start-date-time>] [--end=<end-date-time>] "
            "[--compression=none|gzip|bz2] [--export-cache] "
            "[--output=<output-path>]")
    help = ("Exports the given browse layer specified by either the layer ID "
            "or its browse type. The output is a package, a tar archive, "
            "containing metadata of the browse layer, and all browse reports "
            "and browses that are associated. The processed browse images are "
            "inserted as well. The export can be refined by stating a time "
            "window.")

    def handle(self, *args, **kwargs):
        System.init()
        
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)
        
        # TODO: 
        # - parse parameters
        
        # - query all browses that are within start/stop/layer
        
        # - iterate over all browses in the queryset
        
        #   - get the coverage wrapper from the browse
        
        #   - delete the raster file on the disk
        
        #   - delete the coverage 
        
        #   - delete the browse
        
        #   - delete the browse report (????)
