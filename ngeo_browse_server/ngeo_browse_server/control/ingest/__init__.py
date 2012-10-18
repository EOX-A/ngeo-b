from os.path import isabs, isdir, join
from itertools import product
from numpy import arange

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
from ngeo_browse_server.config.models import (
    RectifiedBrowse, FootprintBrowse, RegularGridBrowse
)


def ingest_browse_report(document):
    """ Ingests a browse report.
    """
    
    # initialize the EOxServer system/registry/configuration
    System.init()
    
    # parse the browse report and create the models
    browse_report, browses = parse_browse_report(document.getroot())
    
    config = get_ngeo_config()
    opt_dir = config.get("control.ingest", "optimized_files_dir")
    if not isabs(opt_dir):
        opt_dir = join(settings.PROJECT_DIR, opt_dir)
    
    # Initialize the format selection and the preprocessor to create 
    # optimized datasets
    format_selection = get_format_selection("GTiff") # TODO: use more options
    preprocessor = WMSPreProcessor(format_selection, bandmode=RGB) # TODO: use options
    
    # initialize the Coverage Manager for Rectified Datasets to register the
    # datasets in the database
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    
    
    for browse in browses:
        # create an output filename to store the optimized file
        output_filename = join(opt_dir, browse.file_name)
        
        # get the srid of the browse and check if the coordinate axes need to 
        # be swapped 
        srid = fromShortCode(browse.reference_system_identifier)
        swap_axes = hasSwappedAxes(srid)
        
        # initialize a GeoReference for the preprocessor
        geo_reference = None
        if type(browse) is RectifiedBrowse:
            geo_reference = Extent(browse.minx, browse.miny, 
                                   browse.maxx, browse.maxy,
                                   srid)
            
        elif type(browse) is FootprintBrowse:
            pixels = parse_coord_list(browse.col_row_list)
            coords = parse_coord_list(browse.coord_list, swap_axes)
            geo_reference = GCPList(zip(pixels, coords), srid)
            
        elif type(browse) is RegularGridBrowse:
            
            range_x = arange(0.0, browse.col_node_number * browse.col_step, browse.col_step)
            range_y = arange(0.0, browse.row_node_number * browse.row_step, browse.row_step)
            
            print browse.col_step, browse.col_node_number
            print browse.row_step, browse.row_node_number
            
            print min(range_x), max(range_x)
            print min(range_y), max(range_y)
            
            # Python is cool!
            pixels = [(x, y) for y in range_y for x in range_x]
            
            coords = []
            for coord_list in browse.coord_lists.all():
                coords.extend(parse_coord_list(coord_list.coord_list, swap_axes))
            
            gcps = [(x, y, pixel, line) 
                    for (x, y), (pixel, line) in zip(coords, pixels)]
            geo_reference = GCPList(gcps, srid)
            
            print srid
        
        # start the preprocessor
        result = preprocessor.process(browse.file_name, output_filename,
                                      geo_reference, generate_metadata=True)
        
        # create EO metadata necessary for registration
        eo_metadata = EOMetadata(
            browse.browse_identifier.id, browse.start_time, browse.end_time,
            result.footprint_geom
        )
        
        # register the optimized dataset
        rect_mgr.create(obj_id=browse.browse_identifier.id, 
                        range_type_name="RGB", default_srid=srid, visible=False,
                        local_path=result.output_filename,
                        eo_metadata=eo_metadata, force=False)
        
        browse.save()
        
    # TODO: add browses to browse report and save all
