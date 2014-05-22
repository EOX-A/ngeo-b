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

import logging
from optparse import make_option
from itertools import izip
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db.models.aggregates import Count
from eoxserver.core.system import System
from eoxserver.core.util.timetools import getDateTime, isotime

from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.config.models import ( 
    BrowseReport, BrowseLayer, Browse
)
from ngeo_browse_server.config.browsereport import data as browsereport_data
from ngeo_browse_server.config.browsereport.serialization import serialize_browse_report
from ngeo_browse_server.config.browselayer import data as browselayer_data
from ngeo_browse_server.config.browselayer.serialization import serialize_browse_layers
from ngeo_browse_server.control.migration import package
from ngeo_browse_server.mapcache import tileset
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.config import get_tileset_path
from ngeo_browse_server.mapcache.tileset import URN_TO_GRID


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):
    
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
                  "as well. Note that this option can not be used with "
                  "browses with merged times.")
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

        logger.info("Starting browse export from command line.")

        browse_layer_id = kwargs.get("browse_layer_id")
        browse_type = kwargs.get("browse_type")
        if not browse_layer_id and not browse_type:
            logger.error("No browse layer or browse type was specified.")
            raise CommandError("No browse layer or browse type was specified.")
        elif browse_layer_id and browse_type:
            logger.error("Both browse layer and browse type were specified.")
            raise CommandError("Both browse layer and browse type were specified.")
        
        start = kwargs.get("start")
        end = kwargs.get("end")
        compression = kwargs.get("compression")
        export_cache = kwargs["export_cache"]
        output_path = kwargs.get("output_path")
        
        # parse start/end if given
        if start: 
            start = getDateTime(start)
        if end:
            end = getDateTime(end)
        
        if not output_path:
            output_path = package.generate_filename(compression)
        
        with package.create(output_path, compression) as p:
            # query the browse layer
            if browse_layer_id:
                try:
                    browse_layer_model = BrowseLayer.objects.get(id=browse_layer_id)
                except BrowseLayer.DoesNotExist:
                    logger.error("Browse layer '%s' does not exist" 
                                 % browse_layer_id)
                    raise CommandError("Browse layer '%s' does not exist" 
                                       % browse_layer_id)
            else:
                try:
                    browse_layer_model = BrowseLayer.objects.get(browse_type=browse_type)
                except BrowseLayer.DoesNotExist:
                    logger.error("Browse layer with browse type '%s' does "
                                 "not exist" % browse_type)
                    raise CommandError("Browse layer with browse type '%s' does "
                                       "not exist" % browse_type)
            
            browse_layer = browselayer_data.BrowseLayer.from_model(browse_layer_model)
            p.set_browse_layer(
                serialize_browse_layers((browse_layer,), pretty_print=True)
            )
            
            # query browse reports; optionally filter for start/end time
            browse_reports_qs = BrowseReport.objects.all()
            
            # apply start/end filter
            if start and not end:
                browse_reports_qs = browse_reports_qs.filter(browses__start_time__gte=start)
            elif end and not start:
                browse_reports_qs = browse_reports_qs.filter(browses__end_time__lte=end)
            elif start and end:
                browse_reports_qs = browse_reports_qs.filter(browses__start_time__gte=start, 
                                                             browses__end_time__lte=end)
            
            # use count annotation to exclude all browse reports with no browses
            browse_reports_qs = browse_reports_qs.annotate(
                browse_count=Count('browses')
            ).filter(browse_layer=browse_layer_model, browse_count__gt=0)
            
            # iterate over all browse reports
            for browse_report_model in browse_reports_qs:
                browses_qs = Browse.objects.filter(
                    browse_report=browse_report_model
                )
                if start:
                    browses_qs = browses_qs.filter(start_time__gte=start)
                if end:
                    browses_qs = browses_qs.filter(end_time__lte=end)
                
                browse_report = browsereport_data.BrowseReport.from_model(
                    browse_report_model, browses_qs
                )
                
                # iterate over all browses in the query
                for browse, browse_model in izip(browse_report, browses_qs):
                    coverage_wrapper = System.getRegistry().getFromFactory(
                        "resources.coverages.wrappers.EOCoverageFactory",
                        {"obj_id": browse_model.coverage_id}
                    )
                    
                    # set the 
                    base_filename = browse_model.coverage_id
                    data_filename = base_filename + ".tif"
                    md_filename = base_filename + ".xml"
                    footprint_filename = base_filename + ".wkb"
                    
                    browse._file_name = data_filename
                    
                    # add optimized browse image to package
                    data_package = coverage_wrapper.getData()
                    data_package.prepareAccess()
                    browse_file_path = data_package.getGDALDatasetIdentifier()
                    with open(browse_file_path) as f:
                        p.add_browse(f, data_filename)
                        wkb = coverage_wrapper.getFootprint().wkb
                        p.add_footprint(footprint_filename, wkb)
                    
                    if export_cache:
                        time_model = mapcache_models.Time.objects.get(
                            start_time__lte=browse_model.start_time,
                            end_time__gte=browse_model.end_time,
                            source__name=browse_layer_model.id
                        )
                        
                        # get "dim" parameter
                        dim = (isotime(time_model.start_time) + "/" +
                               isotime(time_model.end_time))
                        
                        # exit if a merged browse is found
                        if dim != (isotime(browse_model.start_time) + "/" +
                               isotime(browse_model.end_time)):
                            logger.error("Browse layer '%s' contains "
                                         "merged browses and exporting "
                                         "of cache is requested. Try "
                                         "without exporting the cache."
                                         % browse_layer_model.id)
                            raise CommandError("Browse layer '%s' contains "
                                               "merged browses and exporting "
                                               "of cache is requested. Try "
                                               "without exporting the cache."
                                               % browse_layer_model.id)
                        
                        # get path to sqlite tileset and open it
                        ts = tileset.open(
                            get_tileset_path(browse_layer.id)
                        )
                        
                        for tile_desc in ts.get_tiles(
                            browse_layer.id, 
                            URN_TO_GRID[browse_layer.grid], dim=dim,
                            minzoom=browse_layer.highest_map_level,
                            maxzoom=browse_layer.lowest_map_level
                        ):
                            p.add_cache_file(*tile_desc)
                            
                        
                
                # save browse report xml and add it to the package
                p.add_browse_report(
                    serialize_browse_report(browse_report, pretty_print=True),
                    name="%s_%s_%s_%s.xml" % (
                        browse_report.browse_type,
                        browse_report.responsible_org_name,
                        browse_report.date_time.strftime("%Y%m%d%H%M%S%f"),
                        uuid.uuid4().hex
                    )
                )

        logger.info("Successfully finished browse export from command line.")
