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

from os.path import splitext, exists, samefile, dirname
import logging
from lxml import etree
from os import makedirs

from osgeo import gdal
from django.db import transaction

from ngeo_browse_server.exceptions import NGEOException
from ngeo_browse_server.config.browselayer.parsing import parse_browse_layers
from ngeo_browse_server.config.models import BrowseLayer
from ngeo_browse_server.config.browsereport.parsing import parse_browse_report
from ngeo_browse_server.control.migration import package
from ngeo_browse_server.control.queries import (
    get_existing_browse, create_browse_report, create_browse, remove_browse
)
from ngeo_browse_server.control.ingest.config import get_optimized_path
from ngeo_browse_server.control.ingest.filetransaction import FileTransaction
from ngeo_browse_server.control.ingest.result import (
    IngestBrowseResult, IngestBrowseReplaceResult
)
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config
from ngeo_browse_server.mapcache.tasks import seed_mapcache


logger = logging.getLogger(__name__)


class ImportException(NGEOException):
    pass


def import_package(package_path, check_integrity, ignore_cache, config):
    with package.read(package_path) as p:
        browse_layer = parse_browse_layers(etree.parse(p.get_browse_layer()))[0]
        
        # TODO: get browse layer from database and compare values
        
        try:
            browse_layer_model = BrowseLayer.objects.get(
                browse_type=browse_layer.browse_type
            )
        except BrowseLayer.DoesNotExist:
            raise ImportException("The browse layer specified in the package "
                                  "does not exist on this server.")
        
        crs = None
        if browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible":
            crs = "EPSG:3857"
        elif browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad":
            crs = "EPSG:4326"
        
        # TODO: compare browse_layer and browse_layer_model 
        
        if check_integrity:
            
            return
        
        
        for browse_report_file in p.get_browse_reports():
            import_browse_report(p, browse_report_file, browse_layer_model, crs, config)
            

def import_browse_report(p, browse_report_file, browse_layer_model, crs, config):
    browse_report = parse_browse_report(etree.parse(browse_report_file))
    browse_report_model = create_browse_report(browse_report,
                                               browse_layer_model)
    for browse in browse_report:
        print "XXX"
        with transaction.commit_manually():
            with transaction.commit_manually(using="mapcache"):
                try:
                    result = import_browse(p, browse, browse_report_model, browse_layer_model, crs, config)
                except:
                    transaction.rollback()
                    transaction.rollback(using="mapcache")
                    
                    raise
                    continue
            
                transaction.commit() 
                transaction.commit(using="mapcache")
        
        seed_mapcache(tileset=browse_layer_model.id, grid=browse_layer_model.grid, 
                      minx=result.extent[0], miny=result.extent[1],
                      maxx=result.extent[2], maxy=result.extent[3], 
                      minzoom=browse_layer_model.lowest_map_level, 
                      maxzoom=browse_layer_model.highest_map_level,
                      start_time=result.time_interval[0],
                      end_time=result.time_interval[1],
                      delete=False,
                      **get_mapcache_seed_config(config))
        logger.info("Successfully finished seeding.")
            

def import_browse(p, browse, browse_report_model, browse_layer_model, crs, config):
    filename = browse.file_name
    coverage_id = splitext(filename)[0]
    md_filename = coverage_id + ".xml"
    print filename
    
    logger.info("Importing browse with data file '%s' and metadata file '%s'." 
                % (filename, md_filename))
    
    existing_browse_model = get_existing_browse(browse, browse_layer_model.id)
    if existing_browse_model:
        identifier = existing_browse_model.browse_identifier
        if (identifier and browse.identifier
            and  identifier.value != browse.identifier):
            raise ImportException("Existing browse does not have the same "
                                  "browse ID as the ingested.") 
        
        replaced_time_interval = (existing_browse_model.start_time,
                                  existing_browse_model.end_time)
        
        # TODO: implement
        replaced_extent, replaced_filename = remove_browse(
            existing_browse_model, browse_layer_model, coverage_id, config
        )
        replaced = True
        logger.info("Existing browse found, replacing it.")
            
    else:
        # A browse with that identifier does not exist, so just create a new one
        logger.info("Creating new browse.")
        replaced_filename = None
        replaced = False
    
    
    output_filename = get_optimized_path(filename)
    output_dir = dirname(output_filename)
    print output_filename, output_dir
    
    if (exists(output_filename) and 
        ((replaced_filename and
          not samefile(output_filename, replaced_filename))
         or not replaced_filename)):
        raise ImportException("")
    
    with FileTransaction(output_filename):
        try: makedirs(dirname(output_filename))
        except OSError: pass
        
        p.extract_browse_file(filename, output_filename)
        
        # TODO: find out num bands and footprint
        
        ds = gdal.Open(output_filename)
        num_bands = ds.RasterCount
        
        _, _, _, footprint = p.get_browse_metadata(md_filename)
        
        extent, time_interval = create_browse(
            browse, browse_report_model, browse_layer_model,
            coverage_id, crs, replaced, footprint, num_bands, 
            output_filename, config=config
        )
        
        
    if not replaced:
        return IngestBrowseResult(browse.browse_identifier, extent,
                                  time_interval)
    
    else:
        return IngestBrowseReplaceResult(browse.browse_identifier, 
                                         extent, time_interval, replaced_extent, 
                                         replaced_time_interval)

    
    # TODO: ingest browse report