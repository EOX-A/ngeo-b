from os.path import isabs, isdir, join
from itertools import product
from numpy import arange

from django.conf import settings
from eoxserver.core.system import System
from eoxserver.processing.preprocessing import WMSPreProcessor, RGB
from eoxserver.processing.preprocessing.format import get_format_selection
from eoxserver.processing.preprocessing.georeference import Extent, GCPList

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.ingest.parsing import (
    parse_browse_report, parse_coord_list
)
from ngeo_browse_server.config.models import (
    RectifiedBrowse, FootprintBrowse, RegularGridBrowse
)


def ingest_browse_report(document):
    System.init()
    
    browse_report, browses = parse_browse_report(document.getroot())
    
    config = get_ngeo_config()
    opt_dir = config.get("control.ingest", "optimized_files_dir")
    if not isabs(opt_dir):
        opt_dir = join(settings.PROJECT_DIR, opt_dir)
    
    
    format_selection = get_format_selection("GTiff") # TODO: use options
    preprocessor = WMSPreProcessor(format_selection, bandmode=RGB) # TODO: use options
    
    
    for browse in browses:
        output_filename = join(opt_dir, browse.file_name)
        
        geo_reference = None
        if type(browse) is RectifiedBrowse:
            geo_reference = Extent(browse.minx, browse.miny, 
                                   browse.maxx, browse.maxy)
            
        elif type(browse) is FootprintBrowse:
            pixels = parse_coord_list(browse.col_row_list)
            coords = parse_coord_list(browse.coord_list)
            geo_reference = GCPList(zip(pixels, coords)) # TODO srid
            
        elif type(browse) is RegularGridBrowse:
            pixels = product(arange(0.0, browse.col_node_number * browse.col_step),
                             arange(0.0, browse.row_node_number * browse.row_step))
            
            coords = []
            for coord_list in browse.coor_lists:
                coords.extend(parse_coord_list(coord_list.coord_list))
            
            gcps = [(x, y, pixel, line) 
                    for (x, y), (pixel, line) in zip(coords, pixels)]
            geo_reference = GCPList(gcps) # TODO srid
        
        # TODO: refine
        result = preprocessor.process(browse.file_name, output_filename,
                                      geo_reference, True,
                                      browse.browse_identifier.id, 
                                      browse.start_time, browse.end_time)
        
        # TODO: get coverage manager and create a coverage
        rect_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_dataset"
            }
        )
        
        rect_mgr.create(obj_id="TODO", range_type_name="RGB", default_srid="TODO",
                        visible=False, local_path=result.output_filename, 
                        eo_metadata="")
        
    # TODO: add browses to browse report and save all
