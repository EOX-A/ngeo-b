import sys
from os.path import isabs, isdir, join, basename, splitext
from itertools import product
from numpy import arange
from ConfigParser import NoSectionError, NoOptionError

from django.conf import settings
from eoxserver.core.system import System
from eoxserver.processing.preprocessing import WMSPreProcessor, RGB
from eoxserver.processing.preprocessing.format import get_format_selection
from eoxserver.processing.preprocessing.georeference import Extent, GCPList
from eoxserver.resources.coverages.metadata import EOMetadata
from eoxserver.resources.coverages.crss import fromShortCode, hasSwappedAxes

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.ingest.parsing import (
    parse_browse_report, parse_coord_list
)
from ngeo_browse_server.control.ingest import data
from ngeo_browse_server.config import models



def _model_from_parsed(parsed_browse, browse_report, model_cls):
    return model_cls.objects.create(browse_report=browse_report,
                                    **parsed_browse.get_kwargs())


def get_optimized_filename(file_name, path_prefix=None):
    """ Returns an absolute path to a filename within the storage directory for
    optimized raster files. Uses the path prefix if given, otherwise uses the
    'control.ingest.optimized_files_dir' setting from the ngEO configuration.
    
    Also tries to get the postfix for optimized files from the 
    'control.ingest.optimized_files_postfix' setting from the ngEO configuration.
    """
    file_name = basename(file_name)
    config = get_ngeo_config()
    if not path_prefix:
        opt_dir = config.get("control.ingest", "optimized_files_dir")
        
        if not isabs(opt_dir):
            opt_dir = join(settings.PROJECT_DIR, opt_dir)
    else:
        opt_dir = path_prefix
    
    try:
        postfix = config.get("control.ingest", "optimized_files_postfix")
    except NoSectionError, NoOptionError:
        postfix = ""
    
    root, ext = splitext(file_name)
    return join(opt_dir, root + postfix + ext)


def ingest_browse_report(parsed_browse_report, path_prefix=None, 
                         browse_path=None, reraise_exceptions=False):
    """ Ingests a browse report. reraise_exceptions if errors shall be handled 
    externally
    """
    
    # initialize the EOxServer system/registry/configuration
    System.init()
    
    format_selection = get_format_selection("GTiff") # TODO: use more options
    preprocessor = WMSPreProcessor(format_selection, bandmode=RGB) # TODO: use options
    
    browse_type, _ = models.BrowseType.objects.get_or_create(id=parsed_browse_report.browse_type)
    browse_report = models.BrowseReport.objects.create(browse_type=browse_type,
                                                       **parsed_browse_report.get_kwargs())
    
    result = IngestResult()
    
    for parsed_browse in parsed_browse_report:
        try:
            replaced = ingest_browse(parsed_browse, browse_report, preprocessor,
                                     path_prefix, browse_path)
            result.add(parsed_browse.browse_identifier, replaced)
        except Exception, e:
            if reraise_exceptions:
                info = sys.exc_info()
                raise info[0], info[1], info[2]
            else:
                # TODO: use transaction savepoints to keep the DB in a 
                # consistent state
                result.add_failure(parsed_browse.browse_identifier, 
                                   type(e).__name__, str(e))
        
    return result
    

def ingest_browse(parsed_browse, browse_report, preprocessor, 
                  path_prefix=None, browse_path=None):
    """ Ingests a single browse report, performs the preprocessing of the data
    file and adds the generated browse model to the browse report model. Returns
    a boolean value, indicating whether or not the browse has been inserted or
    replaced a previous browse entry.
    """
    replaced = False
    output_filename = get_optimized_filename(parsed_browse.file_name,
                                             path_prefix) 
    
    srid = fromShortCode(parsed_browse.reference_system_identifier)
    swap_axes = hasSwappedAxes(srid)
    
    # check if a browse already exists and delete it in order to replace it
    try:
        browse = models.Browse.objects.get(browse_identifier__id=parsed_browse.browse_identifier)
        browse.delete()
        replaced = True
    except models.Browse.DoesNotExist:
        pass
    
    
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
    
    if parsed_browse.browse_identifier is not None:
        models.BrowseIdentifier.objects.create(id=parsed_browse.browse_identifier, 
                                               browse=model) 

    
    # start the preprocessor
    filename = parsed_browse.file_name
    if browse_path:
        filename = join(browse_path, filename)
    result = preprocessor.process(filename, output_filename,
                                  geo_reference, generate_metadata=True)
    
    # create EO metadata necessary for registration
    eo_metadata = EOMetadata(
        parsed_browse.browse_identifier, parsed_browse.start_time, 
        parsed_browse.end_time, result.footprint_geom
    )
    
    # initialize the Coverage Manager for Rectified Datasets to register the
    # datasets in the database
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    
    # get dataset series ID from browse layer, if available
    container_ids = []
    browse_layer = browse_report.browse_type.browse_layer
    if browse_report.browse_type.browse_layer:
        container_ids.append(browse_layer.id)
    
    # register the optimized dataset
    rect_mgr.create(obj_id=parsed_browse.browse_identifier, 
                    range_type_name="RGB", default_srid=srid, visible=False,
                    local_path=result.output_filename,
                    eo_metadata=eo_metadata, force=False, 
                    container_ids=container_ids)
    
    return replaced

#===============================================================================
# ingestion results
#===============================================================================

class IngestResult(object):
    """ Result object for ingestion operations. """
    
    def __init__(self):
        self._inserted = 0
        self._replaced = 0
        self._records = []
        self._message = "" # TODO: automatically generate error message?
    
    
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
    
    to_be_replaced = property(lambda self: len(self._records)) # TODO: sure?    
    actually_inserted = property(lambda self: self._inserted)
    actually_replaced = property(lambda self: self._replaced)

    