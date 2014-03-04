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
from ngeo_browse_server.config.browselayer.decoding import decode_browse_layers
from ngeo_browse_server.config.models import BrowseLayer, BrowseIdentifier
from ngeo_browse_server.config.browsereport.decoding import decode_browse_report
from ngeo_browse_server.control.migration import package
from ngeo_browse_server.control.ingest.exceptions import IngestionException # Dirty hack to work around circular import
from ngeo_browse_server.control.queries import (
    get_existing_browse, create_browse_report, create_browse, remove_browse
)
from ngeo_browse_server.control.ingest.config import get_optimized_path
from ngeo_browse_server.filetransaction import FileTransaction
from ngeo_browse_server.control.ingest.result import (
    IngestBrowseResult, IngestBrowseReplaceResult, IngestBrowseReportResult,
    IngestBrowseFailureResult
)
from ngeo_browse_server.mapcache.config import (
    get_mapcache_seed_config, get_tileset_path
)
from ngeo_browse_server.mapcache.tasks import seed_mapcache
from eoxserver.core.util.timetools import isotime
from ngeo_browse_server.mapcache.tileset import URN_TO_GRID
from ngeo_browse_server.mapcache import tileset
import traceback


logger = logging.getLogger(__name__)


class ImportException(NGEOException):
    pass


def import_package(package_path, ignore_cache, config):
    with package.read(package_path) as p:
        browse_layer = decode_browse_layers(etree.parse(p.get_browse_layer()))[0]
        
        try:
            browse_layer_model = BrowseLayer.objects.get(
                browse_type=browse_layer.browse_type
            )
        except BrowseLayer.DoesNotExist:
            raise ImportException("The browse layer specified in the package "
                                  "does not exist on this server.")
        
        # check compliance of configuration of browse layers
        check_parameters = [
            "id",
            "browse_type",
            "grid",
            "r_band",
            "g_band",
            "b_band",
            "radiometric_interval_min",
            "radiometric_interval_max",
        ]
        for check_parameter in check_parameters:
            if getattr(browse_layer, check_parameter) != getattr(browse_layer_model, check_parameter):
                raise ImportException("The '%s' configuration of the browse "
                                      "layer specified in the package does not "
                                      "match the one of the browse layer on "
                                      "this server. %s %s" % (check_parameter, getattr(browse_layer, check_parameter), getattr(browse_layer_model, check_parameter)))
        
        crs = None
        if browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible":
            crs = "EPSG:3857"
        elif browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad":
            crs = "EPSG:4326"
        
        import_cache_levels = []
        seed_cache_levels = []
        
        if not p.has_cache() or ignore_cache:
            seed_cache_levels.append((browse_layer_model.lowest_map_level, 
                                      browse_layer_model.highest_map_level))
        else:
            if browse_layer_model.lowest_map_level < browse_layer.lowest_map_level:
                seed_cache_levels.append((browse_layer_model.lowest_map_level,
                                          browse_layer.lowest_map_level))
            
            if browse_layer_model.highest_map_level > browse_layer.highest_map_level:
                seed_cache_levels.append((browse_layer.highest_map_level,
                                          browse_layer_model.highest_map_level))
            
            import_cache_levels.append((max(browse_layer_model.lowest_map_level,
                                            browse_layer.lowest_map_level),
                                        min(browse_layer_model.highest_map_level,
                                            browse_layer.highest_map_level)))
        
        logger.debug("Importing cache levels %s" %import_cache_levels)
        logger.debug("Seeding cache levels %s" %seed_cache_levels)
        
        
        for browse_report_file in p.get_browse_reports():
            import_browse_report(p, browse_report_file, browse_layer_model, crs,
                                 seed_cache_levels, import_cache_levels, config)


def import_browse_report(p, browse_report_file, browse_layer_model, crs,
                         seed_cache_levels, import_cache_levels, config):
    """ 
    """
    
    seed_areas = []
    
    report_result = IngestBrowseReportResult()
    
    browse_report = decode_browse_report(etree.parse(browse_report_file))
    browse_report_model = create_browse_report(browse_report,
                                               browse_layer_model)
    for browse in browse_report:
        with transaction.commit_manually():
            with transaction.commit_manually(using="mapcache"):
                try:
                    
                    result = import_browse(p, browse, browse_report_model,
                                           browse_layer_model, crs, seed_areas,
                                           config)
                    report_result.add(result)
                    
                    transaction.commit() 
                    transaction.commit(using="mapcache")
                    
                except Exception, e:
                    logger.error("Failure during import of browse '%s'." %
                                 browse.browse_identifier)
                    logger.debug(traceback.format_exc() + "\n")
                    transaction.rollback()
                    transaction.rollback(using="mapcache")
                    
                    report_result.add(IngestBrowseFailureResult(
                        browse.browse_identifier, 
                        type(e).__name__, str(e))
                    )
                    
                    continue
        
        tileset_name = browse_layer_model.id
        dim = isotime(browse.start_time) + "/" + isotime(browse.end_time)
        ts = tileset.open(get_tileset_path(tileset_name, config), mode="w")
        
        grid = URN_TO_GRID[browse_layer_model.grid]
        tile_num = 0
        
        # import cache
        for minzoom, maxzoom in import_cache_levels:
            logger.info("Importing cached tiles from zoom level %d to %d." 
                        % (minzoom, maxzoom))
            
            for x, y, z, f in p.get_cache_files(tileset_name, grid, dim):
                if z < minzoom or z > maxzoom:
                    continue
                
                ts.add_tile(tileset_name, grid, dim, x, y, z, f)
                tile_num += 1

        logger.info("Imported %d cached tiles." % tile_num)
        
        # seed cache
        for minzoom, maxzoom in seed_cache_levels:
            logger.info("Re-seeding tile cache from zoom level %d to %d."
                        % (minzoom, maxzoom))
            
            seed_mapcache(tileset=browse_layer_model.id,
                          grid=browse_layer_model.grid, 
                          minx=result.extent[0], miny=result.extent[1],
                          maxx=result.extent[2], maxy=result.extent[3], 
                          minzoom=minzoom, 
                          maxzoom=maxzoom,
                          start_time=result.time_interval[0],
                          end_time=result.time_interval[1],
                          delete=False,
                          **get_mapcache_seed_config(config))
        
            logger.info("Successfully finished seeding.")


def import_browse(p, browse, browse_report_model, browse_layer_model, crs, 
                  seed_areas, config):
    filename = browse.file_name
    coverage_id = splitext(filename)[0]
    footprint_filename = coverage_id + ".wkb"
    
    logger.info("Importing browse with data file '%s' and metadata file '%s'." 
                % (filename, footprint_filename))
    replaced = False
    replaced_filename = None
    
    existing_browse_model = get_existing_browse(browse, browse_layer_model.id)
    if existing_browse_model:
        # check that browse identifiers are equal if present
        try:
            identifier = existing_browse_model.browse_identifier
        except BrowseIdentifier.DoesNotExist:
            identifier = None
        if (identifier and browse.browse_identifier
            and  identifier.value != browse.browse_identifier):
            raise ImportException("Existing browse does not have the same "
                                  "browse ID as the one to import.")
        
        logger.info("Existing browse found, replacing it.")
        
        replaced_extent, replaced_filename = remove_browse(
            existing_browse_model, browse_layer_model, coverage_id, seed_areas,
            config
        )
        replaced = True
    
    else:
        # A browse with that identifier does not exist, so just create a new one
        logger.info("Creating new browse.")
    
    output_filename = get_optimized_path(filename, browse_layer_model.id, config=config)
    
    if (exists(output_filename) and 
        ((replaced_filename and
          not samefile(output_filename, replaced_filename))
         or not replaced_filename)):
        raise ImportException("Output file '%s' already exists and is not to "
                              "be replaced." % output_filename)
    
    with FileTransaction((output_filename, replaced_filename)):
        if not exists(dirname(output_filename)):
            makedirs(dirname(output_filename))
        
        p.extract_browse_file(filename, output_filename)
        
        # TODO: find out num bands and footprint
        ds = gdal.Open(output_filename)
        num_bands = ds.RasterCount
        
        footprint = p.get_footprint(footprint_filename)
        
        extent, time_interval = create_browse(
            browse, browse_report_model, browse_layer_model,
            coverage_id, crs, replaced, footprint, num_bands, 
            output_filename, seed_areas, config=config
        )
    
    if not replaced:
        return IngestBrowseResult(browse.browse_identifier, extent,
                                  time_interval)
    else:
        replaced_time_interval = (existing_browse_model.start_time,
                                  existing_browse_model.end_time)
        return IngestBrowseReplaceResult(browse.browse_identifier, 
                                         extent, time_interval, replaced_extent, 
                                         replaced_time_interval)
