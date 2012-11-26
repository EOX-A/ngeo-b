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
from os.path import isabs, isdir, join, basename, splitext, abspath, exists
import shutil
import tempfile
from itertools import product
from numpy import arange
import logging
from ConfigParser import NoSectionError, NoOptionError
from uuid import uuid4

from django.conf import settings
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
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.tasks import seed_mapcache
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)

def _model_from_parsed(parsed_browse, browse_report, coverage_id, model_cls):
    return model_cls.objects.create(browse_report=browse_report,
                                    coverage_id=coverage_id,
                                    **parsed_browse.get_kwargs())


def ingest_browse_report(parsed_browse_report, storage_dir=None, 
                         optimized_dir=None, reraise_exceptions=False,
                         do_preprocessing=True):
    """ Ingests a browse report. reraise_exceptions if errors shall be handled 
    externally
    """
    
    # initialize the EOxServer system/registry/configuration
    System.init()
    
    try:
        browse_layer = models.BrowseLayer.objects.get(browse_type=parsed_browse_report.browse_type)
    except models.BrowseLayer.DoesNotExist:
        raise Exception("Browse layer with browse type '%s' does not exist."
                        % parsed_browse_report.browse_type) # TODO: raise better exception type?
    
    browse_report = models.BrowseReport.objects.create(browse_layer=browse_layer,
                                                       **parsed_browse_report.get_kwargs())
    
    
    # initialize the preprocessor with configuration values
    crs = None
    if browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible":
        crs = "EPSG:3857"
    elif browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad":
        crs = "EPSG:4326"
        
    logger.debug("Using CRS '%s' ('%s')." % (crs, browse_layer.grid))
    
    
    format_selection = get_format_selection("GTiff", **get_format_config())
    if do_preprocessing:
        preprocessor = WMSPreProcessor(format_selection, crs=crs, bandmode=RGB,
                                       **get_optimization_config())
    else:
        preprocessor = None # TODO: CopyPreprocessor
    
    result = IngestResult()
    
    for parsed_browse in parsed_browse_report:
        try:
            replaced = ingest_browse(parsed_browse, browse_report, preprocessor,
                                     crs, storage_dir, optimized_dir)
            result.add(parsed_browse.browse_identifier, replaced)
        except Exception, e:
            logger.error("Failure during ingestion of browse '%s'." %
                         parsed_browse.browse_identifier)
            if reraise_exceptions:
                info = sys.exc_info()
                raise info[0], info[1], info[2]
            else:
                # TODO: use transaction savepoints to keep the DB in a 
                # consistent state
                result.add_failure(parsed_browse.browse_identifier, 
                                   type(e).__name__, str(e))
        
    return result
    

def ingest_browse(parsed_browse, browse_report, preprocessor, crs, 
                  storage_dir=None, optimized_dir=None):
    """ Ingests a single browse report, performs the preprocessing of the data
    file and adds the generated browse model to the browse report model. Returns
    a boolean value, indicating whether or not the browse has been inserted or
    replaced a previous browse entry.
    """
    replaced = False
    
    srid = fromShortCode(parsed_browse.reference_system_identifier)
    swap_axes = hasSwappedAxes(srid)
    
    config = get_ngeo_config()
    
    browse_layer = browse_report.browse_layer
    coverage_id = parsed_browse.browse_identifier
    if not coverage_id:
        # no identifier given, generate a new one
        prefix = safe_get(config, "control.ingest", "id_prefix", "browse")
        coverage_id = "%s_%s" % (prefix, uuid4().hex)
        logger.info("No browse identifier given, generating coverage ID '%s'."
                    % coverage_id)
    else:
        try:
            NCNameValidator(coverage_id)
        except ValidationError:
            # given ID is not valid, generate a new identifier
            old_id = coverage_id
            prefix = safe_get(config, "control.ingest", "id_prefix", "browse")
            coverage_id = "%s_%s" % (prefix, uuid4().hex)
            logger.info("Browse ID '%s' is not a valid coverage ID. Using "
                        "generated ID '%s'." % (old_id, coverage_id))
        
    # check if a browse already exists and delete it in order to replace it
    try:
        if parsed_browse.browse_identifier:
            # try to get a previous browse
            browse = models.Browse.objects.get(
                browse_identifier__id=parsed_browse.browse_identifier
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
            rect_mgr.delete(obj_id=browse.coverage_id)
            
            browse.delete()
            
            replaced = True
            logger.info("Existing browse found, replacing it.")
            
    except models.Browse.DoesNotExist:
        # A browse with that identifier does not exist, so just create a new one
        logger.info("Creating new browse.")
    
    
    # initialize a GeoReference for the preprocessor
    geo_reference = None
    if type(parsed_browse) is data.RectifiedBrowse:
        geo_reference = Extent(parsed_browse.minx, parsed_browse.miny, 
                               parsed_browse.maxx, parsed_browse.maxy,
                               srid)
        model = _model_from_parsed(parsed_browse, browse_report, coverage_id,
                                   models.RectifiedBrowse)
        
    elif type(parsed_browse) is data.FootprintBrowse:
        # Generate GCPs from footprint coordinates
        pixels = parse_coord_list(parsed_browse.col_row_list)
        coords = parse_coord_list(parsed_browse.coord_list, swap_axes)
        gcps = [(x, y, pixel, line) 
                for (x, y), (pixel, line) in zip(coords, pixels)]
        geo_reference = GCPList(gcps, srid)
        
        model = _model_from_parsed(parsed_browse, browse_report, coverage_id,
                                   models.FootprintBrowse)
        
    elif type(parsed_browse) is data.RegularGridBrowse:
        # calculate a list of pixel coordinates according to the values of the
        # parsed browse report (col_node_number * row_node_number)
        range_x = arange(0.0, parsed_browse.col_node_number * parsed_browse.col_step, parsed_browse.col_step)
        range_y = arange(0.0, parsed_browse.row_node_number * parsed_browse.row_step, parsed_browse.row_step)
        
        # Python is cool!
        pixels = [(x, y) for y in range_y for x in range_x]
        
        # get the lat-lon coordinates as tuple-lists
        coords = []
        for coord_list in parsed_browse.coord_lists:
            coords.extend(parse_coord_list(coord_list, swap_axes))
        
        gcps = [(x, y, pixel, line) 
                for (x, y), (pixel, line) in zip(coords, pixels)]
        geo_reference = GCPList(gcps, srid)
        
        model = _model_from_parsed(parsed_browse, browse_report, coverage_id,
                                   models.RegularGridBrowse)
        
        for coord_list in parsed_browse.coord_lists:
            models.RegularGridCoordList.objects.create(regular_grid_browse=model,
                                                       coord_list=coord_list)
    
    else:
        raise NotImplementedError
    
    # if the browse contains an identifier, create the according model
    if parsed_browse.browse_identifier is not None:
        models.BrowseIdentifier.objects.create(id=parsed_browse.browse_identifier, 
                                               browse=model)

    # start the preprocessor
    input_filename = get_storage_path(parsed_browse.file_name, storage_dir)
    output_filename = get_optimized_path(parsed_browse.file_name, optimized_dir)
    
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
            
            logger.info("Creating database models.")
            create_models(parsed_browse, browse_report, coverage_id, srid, crs,
                          replaced, result)
        
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
                    makedirs(failure_dir)
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
                        makedirs(success_dir)
                        shutil.move(input_filename, success_dir)
                    except:
                        logger.warn("Could not move '%s' to configured "
                                    "`success_dir` '%s'."
                                    % (input_filename, success_dir))
            
    logger.info("Successfully ingested browse with coverage ID '%s'."
                % coverage_id)
    
    return replaced


def create_models(parsed_browse, browse_report, coverage_id, srid, crs,
                  replaced, preprocess_result):
    # initialize the Coverage Manager for Rectified Datasets to register the
    # datasets in the database
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    
    browse_layer = browse_report.browse_layer
    
    # create EO metadata necessary for registration
    eo_metadata = EOMetadata(
        coverage_id, parsed_browse.start_time, parsed_browse.end_time,
        preprocess_result.footprint_geom
    )
    
    
    # get dataset series ID from browse layer, if available
    container_ids = []
    if browse_layer:
        container_ids.append(browse_layer.id)
    
    # register the optimized dataset
    logger.info("Creating Rectified Dataset.")
    coverage = rect_mgr.create(obj_id=coverage_id, range_type_name="RGB", 
                               default_srid=srid, visible=False, 
                               local_path=preprocess_result.output_filename,
                               eo_metadata=eo_metadata, force=False, 
                               container_ids=container_ids)
    
    extent = coverage.getExtent()
    
    # create mapcache models
    source, _ = mapcache_models.Source.objects.get_or_create(name=browse_layer.id)
    mapcache_models.Time.objects.create(start_time=parsed_browse.start_time,
                                        end_time=parsed_browse.end_time,
                                        source=source)
    
    # seed MapCache synchronously
    # TODO: maybe replace this with an async solution
    seed_mapcache(tileset=browse_layer.id, grid=browse_layer.grid, 
                  minx=extent[0], miny=extent[1],
                  maxx=extent[2], maxy=extent[3], 
                  minzoom=browse_layer.lowest_map_level, 
                  maxzoom=browse_layer.highest_map_level,
                  **get_mapcache_config())
    
#===============================================================================
# Ingestion Transaction
#===============================================================================

class IngestionTransaction(object):
    """ File Transaction guard to save previous files for a critical section to
    be used with the "with"-statement.
    """
    
    def __init__(self, subject_filename, safe_filename=None):
        self._subject_filename = subject_filename
        self._safe_filename = safe_filename
    
    
    def __enter__(self):
        " Start of critical block. Check if file exists and create backup. "
        
        # check if the file in question exists. If it does, move it to a safe 
        # location 
        self._exists = exists(self._subject_filename)
        if not self._exists:
            # file does not exist, do nothing
            logger.debug("IngestionTransaction: file '%s' does not exist. "
                         "Do nothing." % self._subject_filename)
            return
        
        # create a temporary file if no path was given
        if not self._safe_filename:
            _, self._safe_filename = tempfile.mkstemp()
            logger.debug("IngestionTransaction: generating backup file '%s'."
                         % self._safe_filename)
        
        logger.debug("IngestionTransaction:Moving '%s' to '%s'." 
                     % (self._subject_filename, self._safe_filename))
        
        # move the old file to a safe location
        shutil.move(self._subject_filename, self._safe_filename)
    
    
    def __exit__(self, etype, value, traceback):
        " End of critical block. Either revert changes or delete backup. "

        if (etype, value, traceback) == (None, None, None):
            # no error occurred
            logger.debug("IngestionTransaction: no error occurred.")
            if self._exists:
                # delete the saved old file, if it existed
                logger.debug("IngestionTransaction: deleting backup '%s'."
                             % self._safe_filename)
                remove(self._safe_filename)
        
        # on error
        else:
            # an error occurred, try removing the new file. It may not exist.
            try:
                logger.debug("IngestionTransaction: An error occurred. " 
                             "Deleting '%s'."
                             % self._subject_filename)
                remove(self._subject_filename)
            except OSError:
                pass
            
            # move the backup file back to restore the initial condition
            if self._exists:
                logger.debug("IngestionTransaction: Restoring backup '%s'."
                             % self._safe_filename)
                shutil.move(self._safe_filename, self._subject_filename)
