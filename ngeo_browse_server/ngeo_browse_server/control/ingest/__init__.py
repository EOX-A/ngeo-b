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
from os.path import exists, dirname, join, isdir, samefile
import shutil
from numpy import arange
import logging
import traceback

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.template.loader import render_to_string
from eoxserver.core.system import System
from eoxserver.processing.preprocessing import WMSPreProcessor, RGB, RGBA, ORIG_BANDS
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
from ngeo_browse_server.control.ingest.result import (
    IngestBrowseReportResult, IngestBrowseResult, IngestBrowseReplaceResult,
    IngestBrowseFailureResult
)
from ngeo_browse_server.control.ingest.config import (
    get_project_relative_path, get_storage_path, get_optimized_path, 
    get_format_config, get_optimization_config, get_mapcache_config
)
from ngeo_browse_server.control.ingest.filetransaction import (
    IngestionTransaction
)
from ngeo_browse_server.control.ingest.config import (
    get_success_dir, get_failure_dir
)
from ngeo_browse_server.control.ingest.exceptions import IngestionException
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.tasks import seed_mapcache


logger = logging.getLogger(__name__)

#===============================================================================
# main functions
#===============================================================================

def ingest_browse_report(parsed_browse_report, do_preprocessing=True, config=None):
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
        # add config parameters and custom params
        params = get_optimization_config(config)
        
        # add radiometric interval
        rad_min = browse_layer.radiometric_interval_min
        if rad_min is not None:
            params["radiometric_interval_min"] = rad_min
        else:
            rad_min = "min"
        rad_max = browse_layer.radiometric_interval_max
        if rad_max is not None:
            params["radiometric_interval_max"] = rad_max
        else:
            rad_max = "max"
        
        # add band selection
        if (browse_layer.r_band is not None and 
            browse_layer.g_band is not None and 
            browse_layer.b_band is not None):
            
            bands = [(browse_layer.r_band, rad_min, rad_max), 
                     (browse_layer.g_band, rad_min, rad_max), 
                     (browse_layer.b_band, rad_min, rad_max)]
            
            if params["bandmode"] == RGBA:
                # RGBA
                bands.append((0, 0, 0))
            
            params["bands"] = bands
        
        preprocessor = WMSPreProcessor(format_selection, crs=crs, **params)
    else:
        preprocessor = None # TODO: CopyPreprocessor
    
    succeded = []
    failed = []
    
    report_result = IngestBrowseReportResult()
    
    # iterate over all browses in the browse report
    for parsed_browse in parsed_browse_report:
        # transaction management per browse
        with transaction.commit_manually():
            with transaction.commit_manually(using="mapcache"):
                try:
                    # try ingest a single browse and log success
                    result = ingest_browse(parsed_browse, browse_report,
                                           browse_layer, preprocessor, crs,
                                           config=config)
                    
                    report_result.add(result)
                    succeded.append(parsed_browse)
                    
                    # commit here to allow seeding
                    transaction.commit() 
                    transaction.commit(using="mapcache")
                    
                    logger.info("Commited changes to database.")
                    
                    try:
                        
                        # seed MapCache synchronously
                        # TODO: maybe replace this with an async solution
                        seed_mapcache(tileset=browse_layer.id, grid=browse_layer.grid, 
                                      minx=result.extent[0], miny=result.extent[1],
                                      maxx=result.extent[2], maxy=result.extent[3], 
                                      minzoom=browse_layer.lowest_map_level, 
                                      maxzoom=browse_layer.highest_map_level,
                                      start_time=result.time_interval[0],
                                      end_time=result.time_interval[1],
                                      delete=False,
                                      **get_mapcache_config(config))
                        logger.info("Successfully finished seeding.")
                        
                    except Exception, e:
                        logger.warn("Seeding failed: %s" % str(e))
                    
                except Exception, e:
                    # report error
                    logger.error("Failure during ingestion of browse '%s'." %
                                 parsed_browse.browse_identifier)
                    logger.debug(traceback.format_exc() + "\n")
                    
                    # undo latest changes, append the failure and continue
                    report_result.add(IngestBrowseFailureResult(
                        parsed_browse.browse_identifier, 
                        type(e).__name__, str(e))
                    )
                    failed.append(parsed_browse)
                    
                    transaction.rollback()
                    transaction.rollback(using="mapcache")

    
    # generate browse report and save to to success/failure dir
    if len(succeded):
        try:
            succeded_report = data.BrowseReport(
                parsed_browse_report.browse_type, 
                parsed_browse_report.date_time, 
                parsed_browse_report.responsible_org_name, 
                succeded
            )
            _save_result_browse_report(succeded_report, get_success_dir(config))
        
        except Exception, e:
            pass # TODO log warning
            
    
    if len(failed):
        try:
            failed_report = data.BrowseReport(
                parsed_browse_report.browse_type, 
                parsed_browse_report.date_time, 
                parsed_browse_report.responsible_org_name, 
                failed
            )
            _save_result_browse_report(failed_report, get_failure_dir(config))
        
        except Exception, e:
            pass # TODO: log warning

    return report_result
    

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
    replaced_filename = None
    
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
        
        replaced_time_interval = browse.start_time, browse.end_time
        replaced_extent, replaced_filename = cleanup_replaced(
            browse, browse_layer, coverage_id, config
        )
        replaced = True
        logger.info("Existing browse found, replacing it.")
            
    except models.Browse.DoesNotExist:
        # A browse with that identifier does not exist, so just create a new one
        logger.info("Creating new browse.")
    
    # get the `leave_original` setting
    leave_original = False
    try:
        leave_original = config.getboolean("control.ingest", "leave_original")
    except: pass
    
    # get the input and output filenames
    input_filename = get_storage_path(parsed_browse.file_name, config=config)
    output_filename = get_optimized_path(parsed_browse.file_name, 
                                         browse_layer.id, config=config)
    output_filename = preprocessor.generate_filename(output_filename)
    
    try:
        # assert that the output file does not exist (unless it is a to-be 
        # replaced file).
        if (exists(output_filename) and 
            ((replaced_filename and
              not samefile(output_filename, replaced_filename))
             or not replaced_filename)):
            raise IngestionException("Output file '%s' already exists."
                                     % output_filename)
        
        # wrap all file operations with IngestionTransaction
        with IngestionTransaction(output_filename, replaced_filename):
        
            # initialize a GeoReference for the preprocessor
            geo_reference = _georef_from_parsed(parsed_browse)
            
            # assert that the input file exists
            if not exists(input_filename):
                raise IngestionException("Input file '%s' does not exist."
                                         % input_filename)
            
            # check that the output directory exists
            safe_makedirs(dirname(output_filename))
            
            # start the preprocessor
            logger.info("Starting preprocessing on file '%s' to create '%s'."
                        % (input_filename, output_filename))
                 
            result = preprocessor.process(input_filename, output_filename,
                                          geo_reference, generate_metadata=True)
            
            # validate preprocess result
            if result.num_bands not in (1, 3, 4): # color index, RGB, RGBA
                raise IngestionException("Processed browse image has %d bands."
                                         % result.num_bands)
            
            logger.info("Creating database models.")
            extent, time_interval = create_models(parsed_browse, browse_report, 
                                                  browse_layer, coverage_id, 
                                                  crs, replaced, result, 
                                                  config=config)
            
        
    except:
        # save exception info to re-raise it
        exc_info = sys.exc_info()
        
        failure_dir = get_failure_dir(config)
        
        logger.error("Error during ingestion of Browse '%s'. Moving "
                     "original image to '%s'."
                     % (parsed_browse.browse_identifier, failure_dir))
        
        # move the file to failure folder
        try:
            if not leave_original:
                safe_makedirs(failure_dir)
                shutil.move(input_filename, failure_dir)
        except Exception, e:
            logger.warn("Could not move '%s' to configured "
                         "`failure_dir` '%s'. Error was: '%s'."
                         % (input_filename, failure_dir, str(e)))
        
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
                success_dir = get_success_dir(config)
                
                try:
                    safe_makedirs(success_dir)
                    shutil.move(input_filename, success_dir)
                except Exception, e:
                    logger.warn("Could not move '%s' to configured "
                                "`success_dir` '%s'. Error was: '%s'."
                                % (input_filename, success_dir, str(e)))
            
    logger.info("Successfully ingested browse with coverage ID '%s'."
                % coverage_id)
    
    if not replaced:
        return IngestBrowseResult(parsed_browse.browse_identifier, extent,
                                  time_interval)
    
    else:
        return IngestBrowseReplaceResult(parsed_browse.browse_identifier, 
                                         extent, time_interval, replaced_extent, 
                                         replaced_time_interval)



#===============================================================================
# model creation/cleanup functions
#===============================================================================

def cleanup_replaced(browse, browse_layer, coverage_id, config=None):
    """ Delete all models and files associated with a to be replaced browse. 
    Returns the extent of the replaced image.
    """
    
    # get previous extent to "un-seed" MapCache in that area
    rect_ds = System.getRegistry().getFromFactory(
        "resources.coverages.wrappers.EOCoverageFactory",
        {"obj_id": browse.coverage_id}
    )
    replaced_extent = rect_ds.getExtent()
    replaced_filename = rect_ds.getData().getLocation().getPath()
    
    # delete the EOxServer rectified dataset entry
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    rect_mgr.delete(obj_id=browse.coverage_id)
    browse.delete()
    
    
    # unseed here
    try:
        seed_mapcache(tileset=browse_layer.id, grid=browse_layer.grid, 
                      minx=replaced_extent[0], miny=replaced_extent[1],
                      maxx=replaced_extent[2], maxy=replaced_extent[3], 
                      minzoom=browse_layer.lowest_map_level, 
                      maxzoom=browse_layer.highest_map_level,
                      start_time=browse.start_time,
                      end_time=browse.end_time,
                      delete=True,
                      **get_mapcache_config(config))
    
    
    except Exception, e:
        logger.warn("Un-seeding failed: %s" % str(e))
    
    
    # delete *one* of the fitting Time objects
    mapcache_models.Time.objects.filter(
        start_time=browse.start_time,
        end_time=browse.end_time,
        source__name=browse_layer.id
    )[0].delete()
    
    return replaced_extent, replaced_filename


def create_models(parsed_browse, browse_report, browse_layer, coverage_id, crs,
                  replaced, preprocess_result, config=None):
    """ Creates all required database models for the browse and returns the
        calculated extent of the registered coverage.
    """
    
    srid = fromShortCode(parsed_browse.reference_system_identifier)
    
    # create the correct model from the pared browse
    if parsed_browse.geo_type == "rectifiedBrowse":
        browse = _model_from_parsed(parsed_browse, browse_report, browse_layer,
                                    coverage_id, models.RectifiedBrowse)
        browse.full_clean()
        browse.save()
        
    elif parsed_browse.geo_type == "footprintBrowse":
        browse = _model_from_parsed(parsed_browse, browse_report, browse_layer,
                                    coverage_id, models.FootprintBrowse)
        browse.full_clean()
        browse.save()
        
    elif parsed_browse.geo_type == "regularGridBrowse":
        browse = _model_from_parsed(parsed_browse, browse_report, browse_layer,
                                    coverage_id, models.RegularGridBrowse)
        browse.full_clean()
        browse.save()
        
        for coord_list in parsed_browse.coord_lists:
            coord_list = models.RegularGridCoordList(regular_grid_browse=browse,
                                                     coord_list=coord_list)
            coord_list.full_clean()
            coord_list.save()
    
    elif parsed_browse.geo_type == "modelInGeotiffBrowse":
        browse = _model_from_parsed(parsed_browse, browse_report, browse_layer,
                                    coverage_id, models.ModelInGeotiffBrowse)
        browse.full_clean()
        browse.save()
    
    else:
        raise NotImplementedError
    
    # if the browse contains an identifier, create the according model
    if parsed_browse.browse_identifier is not None:
        browse_identifier = models.BrowseIdentifier(
            value=parsed_browse.browse_identifier, browse=browse, 
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
    time = mapcache_models.Time(start_time=browse.start_time,
                                end_time=browse.end_time,
                                source=source)
    time.full_clean()
    time.save()
    
    return extent, (browse.start_time, browse.end_time)

#===============================================================================
# helper functions
#===============================================================================

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
    
    if (parsed_browse.reference_system_identifier == "RAW" and
        parsed_browse.geo_type != "modelInGeotiffBrowse"):
        raise IngestionException("Given referenceSystemIdentifier '%s' not "
                                 "valid for a '%s'."
                                 % (parsed_browse.reference_system_identifier,
                                    parsed_browse.geo_type))
    
    if srid is None and parsed_browse.reference_system_identifier != "RAW":
        raise IngestionException("Given referenceSystemIdentifier '%s' not valid."
                                 % parsed_browse.reference_system_identifier)
    
    swap_axes = hasSwappedAxes(srid)
    
    if parsed_browse.geo_type == "rectifiedBrowse":
        coords = parse_coord_list(parsed_browse.coord_list, swap_axes)
        coords = [coord for pair in coords for coord in pair]
        assert(len(coords) == 4)
        return Extent(*coords, srid=srid)
        
    elif parsed_browse.geo_type == "footprintBrowse":
        # Generate GCPs from footprint coordinates
        pixels = parse_coord_list(parsed_browse.col_row_list)
        coords = parse_coord_list(parsed_browse.coord_list, swap_axes)
        assert(len(pixels) == len(coords))
        gcps = [(x, y, pixel, line) 
                for (x, y), (pixel, line) in zip(coords, pixels)]
        
        # check that the last point of the footprint is the first
        if not gcps[0] == gcps[-1]:
            raise IngestionException("The last value of the footprint is not "
                                     "equal to the first.")
        gcps.pop()
        
        return GCPList(gcps, srid)
        
        
    elif parsed_browse.geo_type == "regularGridBrowse":
        # calculate a list of pixel coordinates according to the values of the
        # parsed browse report (col_node_number * row_node_number)
        range_x = arange(
            0.0, parsed_browse.row_node_number * parsed_browse.row_step,
            parsed_browse.row_step
        )
        range_y = arange(
            0.0, parsed_browse.col_node_number * parsed_browse.col_step,
            parsed_browse.col_step
        )
        
        # Python is cool!
        pixels = [(x, y) for x in range_x for y in range_y]
        
        # get the lat-lon coordinates as tuple-lists
        coords = []
        for coord_list in parsed_browse.coord_lists:
            coords.extend(parse_coord_list(coord_list, swap_axes))
        
        # check validity of regularGrid
        if ((len(parsed_browse.coord_lists) != parsed_browse.row_node_number) or 
           (len(coords)/len(parsed_browse.coord_lists) != parsed_browse.col_node_number)):
            raise IngestionException("Invalid regularGrid.")
        
        gcps = [(x, y, pixel, line) 
                for (x, y), (pixel, line) in zip(coords, pixels)]
        return GCPList(gcps, srid)
    
    elif parsed_browse.geo_type == "modelInGeotiffBrowse":
        return None
    
    else:
        raise NotImplementedError


def _generate_coverage_id(parsed_browse, browse_layer):
    frmt = "%Y%m%d%H%M%S%f"
    return "%s_%s_%s" % (browse_layer.id,
                         parsed_browse.start_time.strftime(frmt),
                         parsed_browse.end_time.strftime(frmt))


def _save_result_browse_report(browse_report, path):
    "Render the browse report to the template and save it under the given path."
    
    if isdir(path):
        # generate a filename
        path = join(path, "%s_%s_%s.xml" % (browse_report.browse_type, 
                                            browse_report.responsible_org_name,
                                            browse_report.date_time.strftime("%Y%m%d%H%M%S%f")))
    
    safe_makedirs(dirname(path))
    
    with open(path, "w+") as f:
        f.write(render_to_string("control/browse_report.xml",
                                 {"browse_report": browse_report}))
