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

import sys
from os import remove, makedirs
from os.path import exists, dirname
import shutil
from numpy import arange
import logging
import traceback

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from eoxserver.core.system import System
from eoxserver.processing.preprocessing import WMSPreProcessor, RGB
from eoxserver.processing.preprocessing.format import get_format_selection
from eoxserver.processing.preprocessing.georeference import Extent, GCPList
from eoxserver.resources.coverages.metadata import EOMetadata
from eoxserver.resources.coverages.crss import fromShortCode, hasSwappedAxes
from eoxserver.resources.coverages.models import NCNameValidator

from ngeo_browse_server.config import get_ngeo_config, safe_get
from ngeo_browse_server.config import models
from ngeo_browse_server.control.ingest.parsing import (
    parse_browse_report, parse_coord_list
)
from ngeo_browse_server.control.ingest import data
from ngeo_browse_server.control.ingest.result import IngestResult
from ngeo_browse_server.control.ingest.config import (
    get_project_relative_path, get_storage_path, get_optimized_path, 
    get_format_config, get_optimization_config, get_mapcache_config
)
from ngeo_browse_server.control.ingest.filetransaction import IngestionTransaction
from ngeo_browse_server.control.ingest.exceptions import IngestionException
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.tasks import seed_mapcache


logger = logging.getLogger(__name__)

def safe_makedirs(path):
    """ make dirs without raising an exception when the directories are already
    existing.
    """
    
    if not exists(path):
        makedirs(path)


def _model_from_parsed(parsed_browse, browse_report, browse_layer, 
                       coverage_id, model_cls):
    model = model_cls(browse_report=browse_report, browse_layer=browse_layer, 
                      coverage_id=coverage_id, **parsed_browse.get_kwargs())
    return model


def _georef_from_parsed(parsed_browse):
    srid = fromShortCode(parsed_browse.reference_system_identifier)
    swap_axes = hasSwappedAxes(srid)
    
    if type(parsed_browse) is data.RectifiedBrowse:
        return Extent(parsed_browse.minx, parsed_browse.miny, 
                      parsed_browse.maxx, parsed_browse.maxy,
                      srid)
        
    elif type(parsed_browse) is data.FootprintBrowse:
        # Generate GCPs from footprint coordinates
        pixels = parse_coord_list(parsed_browse.col_row_list)
        coords = parse_coord_list(parsed_browse.coord_list, swap_axes)
        gcps = [(x, y, pixel, line) 
                for (x, y), (pixel, line) in zip(coords, pixels)]
        
        # check that the last point of the footprint is the first
        if not gcps[0] == gcps[-1]:
            raise IngestionException("The last value of the footprint is not "
                                     "equal to the first.")
        
        return GCPList(gcps, srid)
        
        
    elif type(parsed_browse) is data.RegularGridBrowse:
        # calculate a list of pixel coordinates according to the values of the
        # parsed browse report (col_node_number * row_node_number)
        range_x = arange(
            0.0, parsed_browse.col_node_number * parsed_browse.col_step,
            parsed_browse.col_step
        )
        range_y = arange(
            0.0, parsed_browse.row_node_number * parsed_browse.row_step,
            parsed_browse.row_step
        )
        
        # Python is cool!
        pixels = [(x, y) for y in range_y for x in range_x]
        
        # get the lat-lon coordinates as tuple-lists
        coords = []
        for coord_list in parsed_browse.coord_lists:
            coords.extend(parse_coord_list(coord_list, swap_axes))
        
        gcps = [(x, y, pixel, line) 
                for (x, y), (pixel, line) in zip(coords, pixels)]
        return GCPList(gcps, srid)
    
    else:
        raise NotImplementedError

def _generate_coverage_id(parsed_browse, browse_layer):
    frmt = "%Y%m%d%H%M%S%f"
    return "%s_%s_%s" % (browse_layer.id,
                         parsed_browse.start_time.strftime(frmt),
                         parsed_browse.end_time.strftime(frmt))

    

def ingest_browse_report(parsed_browse_report, reraise_exceptions=False,
                         do_preprocessing=True, config=None):
    """ Ingests a browse report. reraise_exceptions if errors shall be handled 
    externally
    """
    
    # initialize the EOxServer system/registry/configuration
    System.init()
    
    try:
        # get the according browse layer
        browse_type = parsed_browse_report.browse_type
        browse_layer = models.BrowseLayer.objects.get(browse_type=browse_type)
    except models.BrowseLayer.DoesNotExist:
        raise IngestionException("Browse layer with browse type '%s' does not "
                                 "exist." % parsed_browse_report.browse_type)
    
    # generate a browse report model
    browse_report = models.BrowseReport(
        browse_layer=browse_layer, **parsed_browse_report.get_kwargs()
    )
    browse_report.full_clean()
    browse_report.save()
    
    # initialize the preprocessor with configuration values
    crs = None
    if browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible":
        crs = "EPSG:3857"
    elif browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad":
        crs = "EPSG:4326"
        
    logger.debug("Using CRS '%s' ('%s')." % (crs, browse_layer.grid))
    
    # create the required preprocessor/format selection
    format_selection = get_format_selection("GTiff",
                                            **get_format_config(config))
    if do_preprocessing:
        preprocessor = WMSPreProcessor(format_selection, crs=crs, bandmode=RGB, # TODO if alpha -> RGBA
                                       **get_optimization_config(config))
    else:
        preprocessor = None # TODO: CopyPreprocessor
    

    # transaction management on browse report basis
    with transaction.commit_on_success():
        result = IngestResult()
        
        # iterate over all browses in the browse report
        for parsed_browse in parsed_browse_report:
            sid = transaction.savepoint()
            try:
                # try ingest a single browse and log success
                replaced = ingest_browse(parsed_browse, browse_report,
                                         browse_layer, preprocessor, crs,
                                         config=config)
                result.add(parsed_browse.browse_identifier, replaced)
                
            except Exception, e:
                # report error
                logger.error("Failure during ingestion of browse '%s'." %
                             parsed_browse.browse_identifier)
                logger.error(traceback.format_exc() + "\n")
                
                if reraise_exceptions:
                    # complete rollback and reraise exception
                    transaction.rollback()
                    
                    info = sys.exc_info()
                    raise info[0], info[1], info[2]
                
                else:
                    # undo latest changes, append the failure and continue
                    transaction.savepoint_rollback(sid)
                    result.add_failure(parsed_browse.browse_identifier, 
                                       type(e).__name__, str(e))
            
            # ingestion of browse was ok, commit changes
            transaction.savepoint_commit(sid)
        
        # ingestion finished, commit changes. 
        transaction.commit()
            
    return result
    

def ingest_browse(parsed_browse, browse_report, browse_layer, preprocessor, crs,
                  config=None):
    """ Ingests a single browse report, performs the preprocessing of the data
    file and adds the generated browse model to the browse report model. Returns
    a boolean value, indicating whether or not the browse has been inserted or
    replaced a previous browse entry.
    """
    
    logger.info("Ingesting browse '%s'."
                % (parsed_browse.browse_identifier or "<<no ID>>"))
    
    replaced = False
    replaced_extent = None
    
    config = config or get_ngeo_config()
    
    coverage_id = parsed_browse.browse_identifier
    if not coverage_id:
        # no identifier given, generate a new one
        coverage_id = _generate_coverage_id(parsed_browse, browse_layer)
        logger.info("No browse identifier given, generating coverage ID '%s'."
                    % coverage_id)
    else:
        try:
            NCNameValidator(coverage_id)
        except ValidationError:
            # given ID is not valid, generate a new identifier
            old_id = coverage_id
            coverage_id = _generate_coverage_id(parsed_browse, browse_layer)
            logger.info("Browse ID '%s' is not a valid coverage ID. Using "
                        "generated ID '%s'." % (old_id, coverage_id))
        
    # check if a browse already exists and delete it in order to replace it
    try:
        browse = None
        if parsed_browse.browse_identifier:
            # try to get a previous browse. IDs are unique within a browse layer
            browse = models.Browse.objects.get(
                browse_identifier__value=parsed_browse.browse_identifier,
                browse_layer=browse_layer
            )
            
        else:
            # if no browse ID is given, try to get the browse by browse layer,
            # start- and end-time
            browse = models.Browse.objects.get(
                start_time=parsed_browse.start_time,
                end_time=parsed_browse.end_time,
                browse_layer=browse_layer
            )
        
        # delete *one* of the fitting Time objects
        mapcache_models.Time.objects.filter(
            start_time=browse.start_time,
            end_time=browse.end_time,
            source__name=browse_layer.id
        )[0].delete()
        
        # delete the EOxServer rectified dataset entry
        rect_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_dataset"
            }
        )
        
        # get previous extent to "un-seed" MapCache in that area
        rect_ds = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": coverage_id}
        )
        replaced_extent = rect_ds.getExtent()
        
        rect_mgr.delete(obj_id=browse.coverage_id)
        
        browse.delete()
        
        replaced = True
        logger.info("Existing browse found, replacing it.")
            
    except models.Browse.DoesNotExist:
        # A browse with that identifier does not exist, so just create a new one
        logger.info("Creating new browse.")
    
    # initialize a GeoReference for the preprocessor
    geo_reference = _georef_from_parsed(parsed_browse)
    
    # start the preprocessor
    input_filename = get_storage_path(parsed_browse.file_name, config=config)
    output_filename = get_optimized_path(parsed_browse.file_name, 
                                         browse_layer.id, config=config)
    output_filename = preprocessor.generate_filename(output_filename)
    
    # assert that the input file exists
    if not exists(input_filename):
        raise IngestionException("Input file '%s' does not exist."
                                 % input_filename)
    
    # assert that the output file does not exist
    if exists(output_filename):
        raise IngestionException("Output file '%s' already exists."
                                 % output_filename)
    
    # check that the output directory exists
    safe_makedirs(dirname(output_filename))
    
    # wrap all file operations with IngestionTransaction
    with IngestionTransaction(output_filename):
        leave_original = False
        try:
            leave_original = config.getboolean("control.ingest", "leave_original")
        except: pass
        
        try:
            logger.info("Starting preprocessing on file '%s' to create '%s'."
                        % (input_filename, output_filename))
                 
            result = preprocessor.process(input_filename, output_filename,
                                          geo_reference, generate_metadata=True)
            
            # validate preprocess result
            if result.num_bands not in (3, 4):
                raise IngestionException("Processed browse image has %d bands."
                                         % result.num_bands)
            
            logger.info("Creating database models.")
            extent = create_models(parsed_browse, browse_report, browse_layer,
                                   coverage_id, crs, replaced, result,
                                   config=config)
            
            
            # "un-seed" if replaced and previous extent not equal to this extent
            if replaced and extent != replaced_extent:
                seed_mapcache(tileset=browse_layer.id, grid=browse_layer.grid, 
                              minx=replaced_extent[0], miny=replaced_extent[1],
                              maxx=replaced_extent[2], maxy=replaced_extent[3], 
                              minzoom=browse_layer.lowest_map_level, 
                              maxzoom=browse_layer.highest_map_level,
                              delete=True,
                              **get_mapcache_config(config))
            
            
            # seed MapCache synchronously
            # TODO: maybe replace this with an async solution
            seed_mapcache(tileset=browse_layer.id, grid=browse_layer.grid, 
                          minx=extent[0], miny=extent[1],
                          maxx=extent[2], maxy=extent[3], 
                          minzoom=browse_layer.lowest_map_level, 
                          maxzoom=browse_layer.highest_map_level,
                          delete=False,
                          **get_mapcache_config(config))
        
        except:
            # save exception info to re-raise it
            exc_info = sys.exc_info()
            
            failure_dir = get_project_relative_path(
                safe_get(config, "control.ingest", "failure_dir")
            )
            
            logger.error("Error during ingestion of Browse '%s'. Moving "
                         "original image to '%s'."
                         % (parsed_browse.browse_identifier, failure_dir))
            
            # move the file to failure folder
            try:
                if not leave_original:
                    safe_makedirs(failure_dir)
                    shutil.move(input_filename, failure_dir)
            except:
                logger.warn("Could not move '%s' to configured `failure_dir` "
                             "'%s'." % (input_filename, failure_dir))
            
            # re-raise the exception
            raise exc_info[0], exc_info[1], exc_info[2]
        
        else:
            # move the file to success folder, or delete it right away
            delete_on_success = False
            try: delete_on_success = config.getboolean("control.ingest", "delete_on_success")
            except: pass
            
            if not leave_original:
                if delete_on_success:
                    remove(input_filename)
                else:
                    success_dir = get_project_relative_path(
                        safe_get(config, "control.ingest", "success_dir")
                    )
                    
                    try:
                        safe_makedirs(success_dir)
                        shutil.move(input_filename, success_dir)
                    except:
                        logger.warn("Could not move '%s' to configured "
                                    "`success_dir` '%s'."
                                    % (input_filename, success_dir))
            
    logger.info("Successfully ingested browse with coverage ID '%s'."
                % coverage_id)
    
    return replaced


def create_models(parsed_browse, browse_report, browse_layer, coverage_id, crs,
                  replaced, preprocess_result, config=None):
    """ Creates all required database models for the browse and returns the
        calculated extent of the registered coverage.
    """
    
    srid = fromShortCode(parsed_browse.reference_system_identifier)
    
    # create the correct model from the pared browse
    if type(parsed_browse) is data.RectifiedBrowse:
        model = _model_from_parsed(parsed_browse, browse_report, browse_layer,
                                   coverage_id, models.RectifiedBrowse)
        
    elif type(parsed_browse) is data.FootprintBrowse:
        model = _model_from_parsed(parsed_browse, browse_report, browse_layer,
                                   coverage_id, models.FootprintBrowse)
        
    elif type(parsed_browse) is data.RegularGridBrowse:
        model = _model_from_parsed(parsed_browse, browse_report, browse_layer,
                                   coverage_id, models.RegularGridBrowse)
        
        for coord_list in parsed_browse.coord_lists:
            coord_list = models.RegularGridCoordList(regular_grid_browse=model,
                                                     coord_list=coord_list)
            coord_list.full_clean()
            coord_list.save()
    
    else:
        raise NotImplementedError
    
    model.full_clean()
    model.save()
    
    # if the browse contains an identifier, create the according model
    if parsed_browse.browse_identifier is not None:
        browse_identifier = models.BrowseIdentifier(
            value=parsed_browse.browse_identifier, browse=model, 
            browse_layer=browse_layer
        )
        browse_identifier.full_clean()
        browse_identifier.save()
    
    # initialize the Coverage Manager for Rectified Datasets to register the
    # datasets in the database
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    
    # create EO metadata necessary for registration
    eo_metadata = EOMetadata(
        coverage_id, parsed_browse.start_time, parsed_browse.end_time,
        preprocess_result.footprint_geom
    )
    
    # get dataset series ID from browse layer, if available
    container_ids = []
    if browse_layer:
        container_ids.append(browse_layer.id)
    
    range_type_name = "RGB" if preprocess_result.num_bands == 3 else "RGBA"
    
    # register the optimized dataset
    logger.info("Creating Rectified Dataset.")
    coverage = rect_mgr.create(obj_id=coverage_id, 
                               range_type_name=range_type_name,
                               default_srid=srid, visible=False, 
                               local_path=preprocess_result.output_filename,
                               eo_metadata=eo_metadata, force=False, 
                               container_ids=container_ids)
    
    extent = coverage.getExtent()
    
    # create mapcache models
    source, _ = mapcache_models.Source.objects.get_or_create(name=browse_layer.id)
    time = mapcache_models.Time(start_time=parsed_browse.start_time,
                                end_time=parsed_browse.end_time,
                                source=source)
    time.full_clean()
    time.save()
    
    return extent

