import sys
from os import remove
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

from ngeo_browse_server.config import get_ngeo_config, safe_get
from ngeo_browse_server.control.ingest.parsing import (
    parse_browse_report, parse_coord_list
)
from ngeo_browse_server.control.ingest import data
from ngeo_browse_server.config import models
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.control.ingest.tasks import seed_mapcache


logger = logging.getLogger(__name__)

def _model_from_parsed(parsed_browse, browse_report, model_cls):
    return model_cls.objects.create(browse_report=browse_report,
                                    **parsed_browse.get_kwargs())

def get_project_relative_path(path):
    if isabs(path):
        return path
    
    return join(settings.PROJECT_DIR, path)


def get_storage_path(file_name, storage_dir=None):
    """ Returns an absolute path to a filename within the intermediary storage
    directory for uploaded but unprocessed files. 
    """
    
    section = "control.ingest"
    
    if not storage_dir:
        storage_dir = get_ngeo_config().get(section, "storage_dir")
    
    return get_project_relative_path(join(storage_dir, file_name))


def get_optimized_path(file_name, optimized_dir=None):
    """ Returns an absolute path to a filename within the storage directory for
    optimized raster files. Uses the optimized directory if given, otherwise 
    uses the 'control.ingest.optimized_files_dir' setting from the ngEO
    configuration.
    
    Also tries to get the postfix for optimized files from the 
    'control.ingest.optimized_files_postfix' setting from the ngEO configuration.
    
    All relative paths are treated relative to the PROJECT_DIR directory setting.
    """
    file_name = basename(file_name)
    config = get_ngeo_config()
    
    section = "control.ingest"
    
    if not optimized_dir:
        optimized_dir = config.get(section, "optimized_files_dir")
        
    optimized_dir = get_project_relative_path(optimized_dir)
    
    try:
        postfix = config.get(section, "optimized_files_postfix")
    except NoSectionError, NoOptionError:
        postfix = ""
    
    root, ext = splitext(file_name)
    return join(optimized_dir, root + postfix + ext)


def get_format_config():
    values = {}
    config = get_ngeo_config()
    
    section = "control.ingest"
    
    values["compression"] = safe_get(config, section, "compression")
    
    if values["compression"] == "JPEG":
        value = safe_get(config, section, "jpeg_quality")
        values["jpeg_quality"] = int(value) if value is not None else None
    
    elif values["compression"] == "DEFLATE":
        value = safe_get(config, section, "zlevel")
        values["zlevel"] = int(value) if value is not None else None
        
    try:
        values["tiling"] = config.getboolean(section, "tiling")
    except: pass
    
    return values


def get_optimization_config():
    values = {}
    config = get_ngeo_config()
    
    section = "control.ingest"
    
    try:
        values["overviews"] = config.getboolean(section, "overviews")
    except: pass
    
    try:
        values["color_index"] = config.getboolean(section, "color_index")
    except: pass
    
    try:
        values["footprint_alpha"] = config.getboolean(section, "footprint_alpha")
    except: pass
    
    return values


def get_mapcache_config():
    values = {}
    config = get_ngeo_config()
    
    section = "control.ingest.mapcache"
    
    values["seed_command"] = config.get(section, "seed_command")
    values["config_file"] = config.get(section, "config_file")
    values["threads"] = int(safe_get(config, section, "threads", 1))
    
    return values
    

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
    # TODO: CopyPreProcessor ??????
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
    
    identifier = parsed_browse.browse_identifier
    if not identifier:
        # generate an identifier
        prefix = safe_get(config, "control.ingest", "id_prefix", "browse")
        identifier = "%s_%s" % (prefix, uuid4().hex)
    else:
        # TODO: check if the browse ID is a valid coverage ID, otherwise replace it
        pass
    
    # check if a browse already exists and delete it in order to replace it
    try:
        if identifier:
            browse = models.Browse.objects.get(browse_identifier__id=identifier)
            browse.delete()
            replaced = True
            logger.info("Replacing browse '%s'." % identifier)
    except models.Browse.DoesNotExist:
        logger.info("Creating new browse '%s'." % identifier)
    
    
    # initialize a GeoReference for the preprocessor
    geo_reference = None
    if type(parsed_browse) is data.RectifiedBrowse:
        geo_reference = Extent(parsed_browse.minx, parsed_browse.miny, 
                               parsed_browse.maxx, parsed_browse.maxy,
                               srid)
        model = _model_from_parsed(parsed_browse, browse_report,
                                   models.RectifiedBrowse)
        
    elif type(parsed_browse) is data.FootprintBrowse:
        pixels = parse_coord_list(parsed_browse.col_row_list)
        coords = parse_coord_list(parsed_browse.coord_list, swap_axes)
        gcps = [(x, y, pixel, line) 
                for (x, y), (pixel, line) in zip(coords, pixels)]
        geo_reference = GCPList(gcps, srid)
        
        model = _model_from_parsed(parsed_browse, browse_report,
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
        
        model = _model_from_parsed(parsed_browse, browse_report,
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
        try:
            logger.info("Starting preprocessing on file '%s' to create '%s'."
                        % (input_filename, output_filename))
                 
            result = preprocessor.process(input_filename, output_filename,
                                          geo_reference, generate_metadata=True)
            
            logger.info("Creating database models.")
            create_models(parsed_browse, browse_report, identifier, srid, crs,
                          replaced, result)
        
        except:
            failure_dir = get_project_relative_path(
                safe_get(config, "control.ingest", "failure_dir")
            )
            
            logger.error("Error during ingestion of Browse '%s'. Moving "
                         "original image to '%s'."
                         % (parsed_browse.browse_identifier, failure_dir))
            
            # move the file to failure folder
            try:
                shutil.move(input_filename, failure_dir)
            except:
                logger.warn("Could not move '%s' to configured `failure_dir` "
                             "'%s'." % (input_filename, failure_dir))
            
            # re-raise the exception
            raise
        
        else:
            # move the file to success folder, or delete it right away
            delete_on_success = False
            try: delete_on_success = config.getboolean("control.ingest", "delete_on_success")
            except: pass
            
            if delete_on_success:
                remove(input_filename)
            else:
                success_dir = get_project_relative_path(
                    safe_get(config, "control.ingest", "success_dir")
                )
                
                try:
                    shutil.move(input_filename, success_dir)
                except:
                    logger.warn("Could not move '%s' to configured "
                                "`success_dir` '%s'."
                                % (input_filename, success_dir))
            
        
    logger.info("Successfully ingested browse with ID '%s'."
                % identifier)
    
    return replaced


def create_models(parsed_browse, browse_report, identifier, srid, crs, replaced,
                  preprocess_result):
    
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    
    # unregister the previous coverage first
    if replaced:
        rect_mgr.delete(obj_id=identifier)
        # TODO: delete the mapcache models here
    
    # create EO metadata necessary for registration
    eo_metadata = EOMetadata(
        identifier, parsed_browse.start_time, parsed_browse.end_time,
        preprocess_result.footprint_geom
    )
    
    # initialize the Coverage Manager for Rectified Datasets to register the
    # datasets in the database
    
    
    logging.info("Creating Rectified Dataset.")
    # get dataset series ID from browse layer, if available
    container_ids = []
    browse_layer = browse_report.browse_layer
    if browse_layer:
        container_ids.append(browse_layer.id)
    
    # register the optimized dataset
    coverage = rect_mgr.create(obj_id=identifier, range_type_name="RGB", 
                               default_srid=srid, visible=False, 
                               local_path=preprocess_result.output_filename,
                               eo_metadata=eo_metadata, force=False, 
                               container_ids=container_ids)
    
    extent = coverage.getExtent()
    
    # TODO: mapcache model replacements??
    # create mapcache models
    source, _ = mapcache_models.Source.objects.get_or_create(name=browse_layer.id)
    time = mapcache_models.Time.objects.create(start_time=parsed_browse.start_time,
                                               end_time=parsed_browse.end_time,
                                               source=source)
    
    mapcache_models.Extent.objects.create(srs=crs,
                                          minx=extent[0], miny=extent[1],
                                          maxx=extent[2], maxy=extent[3],
                                          time=time)
    
    # seed MapCache synchronously
    # TODO: maybe replace this with an async solution
    seed_mapcache(tileset=browse_layer.id, grid=crs, 
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
        " Start of critical block. "
        
        # check if the file in question exists. If it does, move it to a safe 
        # location 
        self._exists = exists(self._subject_filename)
        if not self._exists:
            # file does not exist, do nothing
            return
        
        # create a temporary file if no path was given
        if not self._safe_filename:
            _, self._safe_filename = tempfile.mkstemp()
        
        logger.debug("Moving '%s' to '%s'." % (self._subject_filename,
                                               self._safe_filename))
        
        # move the old file to a safe location
        shutil.move(self._subject_filename, self._safe_filename)
    
    
    def __exit__(self, etype, value, traceback):
        " End of critical block. "
        # no error
        if (etype, value, traceback) == (None, None, None):
            # no error occurred
            if self._exists:
                # delete the saved old file, if it existed
                remove(self._safe_filename)
        
        # on error
        else:
            # an error occurred, try removing the new file. It may not exist.
            try:
                remove(self._subject_filename)
            except OSError:
                pass
            
            # move the backup file back to restore the initial condition
            if self._exists:
                shutil.move(self._safe_filename, self._subject_filename)
            

#===============================================================================
# ingestion results
#===============================================================================

class IngestResult(object):
    """ Result object for ingestion operations. """
    
    def __init__(self):
        self._inserted = 0
        self._replaced = 0
        self._records = []
    
    
    def add(self, identifier, replaced=False, status="success"):
        """ Adds a single browse ingestion result, where the status is either
        success or failure.
        """
        if replaced:
            self._replaced += 1
        else:
            self._inserted += 1
        
        assert(status in ("success", "partial"))
        
        self._records.append((identifier, status, None, None))
    
    
    def add_failure(self, identifier, code, message):
        """ Add a single browse ingestion failure result, whith an according 
        error code and message.
        """
        self._records.append((identifier, "failure", code, message))


    def __iter__(self):
        "Helper for easy iteration of browse ingest results."
        return iter(self._records)
    
    
    @property
    def status(self):
        """Returns 'partial' if any failure results where registered, else 
        'success'.
        """
        if len(filter(lambda record: record[1] == "failure", self._records)):
            return "partial"
        else:
            return "success"
    
    to_be_replaced = property(lambda self: len(self._records))  
    actually_inserted = property(lambda self: self._inserted)
    actually_replaced = property(lambda self: self._replaced)

    