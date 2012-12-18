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
from itertools import izip

from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.control.ingest import data  
from ngeo_browse_server.control.ingest.exceptions import ParsingException


logger = logging.getLogger(__name__)

def ns_rep(tag):
    "Namespacify a given tag name for the use with etree"
    return "{http://ngeo.eo.esa.int/schema/browseReport}" + tag

def ns_bsi(tag):
    "Namespacify a given tag name for the use with etree"
    return "{http://ngeo.eo.esa.int/schema/browse/ingestion}" + tag


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


def parse_browse_report(browse_report):
    """ Parsing function to return a BrowseReport object from an 
        ElementTree.Element node.
    """
    
    logger.info("Start parsing browse report.")
    
    expected_tags = ns_bsi("ingestBrowse"), ns_rep("browseReport")
    if browse_report.tag not in expected_tags:
        raise ParsingException("Invalid root tag '%s'. Expected one of '%s'."
                               % (browse_report.tag, expected_tags),
                               code="parsing")
    
    browse_report = data.BrowseReport(
        date_time=getDateTime(browse_report.find(ns_rep("dateTime")).text),
        browse_type=browse_report.find(ns_rep("browseType")).text,
        responsible_org_name=browse_report.find(ns_rep("responsibleOrgName")).text,
        browses=[parse_browse(browse_elem)
                 for browse_elem in browse_report.iter(ns_rep("browse"))]
    )
    
    logger.info("Finished parsing browse report.")

    return browse_report


def parse_browse(browse_elem, browse_report=None):
    """ Parsing function to return a Browse object from an ElementTree.Element
        node.
    """
    
    # general args
    kwargs = {
        "file_name": browse_elem.find(ns_rep("fileName")).text,
        "image_type": browse_elem.find(ns_rep("imageType")).text,
        "reference_system_identifier": browse_elem.find(ns_rep("referenceSystemIdentifier")).text,
        "start_time": getDateTime(browse_elem.find(ns_rep("startTime")).text),
        "end_time": getDateTime(browse_elem.find(ns_rep("endTime")).text),
    }
    
    browse_identifier = browse_elem.find(ns_rep("browseIdentifier"))
    if browse_identifier is not None:
        kwargs["browse_identifier"] = browse_identifier.text
    
    # check type of geo reference
    rectified_browse = browse_elem.find(ns_rep("rectifiedBrowse"))
    footprint = browse_elem.find(ns_rep("footprint"))
    regular_grid = browse_elem.find(ns_rep("regularGrid"))
    model_in_geotiff = browse_elem.find(ns_rep("modelInGeotiff"))
    vertical_curtain_footprint = browse_elem.find(ns_rep("verticalCurtainFootprint"))
    
    if rectified_browse is not None:
        logger.info("Parsing Rectified Browse.")
        kwargs["coord_list"] = rectified_browse.find(ns_rep("coordList")).text
        return data.RectifiedBrowse(**kwargs)
    
    elif footprint is not None:
        logger.info("Parsing Footprint Browse.")
        kwargs["node_number"] = int(footprint.attrib["nodeNumber"])
        kwargs["col_row_list"] = footprint.find(ns_rep("colRowList")).text
        kwargs["coord_list"] = footprint.find(ns_rep("coordList")).text
        
        return data.FootprintBrowse(**kwargs)
    
    elif regular_grid is not None:
        logger.info("Parsing Regular Grid Browse.")
        kwargs["col_node_number"] = int(regular_grid.find(ns_rep("colNodeNumber")).text)
        kwargs["row_node_number"] = int(regular_grid.find(ns_rep("rowNodeNumber")).text)
        kwargs["col_step"] = float(regular_grid.find(ns_rep("colStep")).text)
        kwargs["row_step"] = float(regular_grid.find(ns_rep("rowStep")).text)
        kwargs["coord_lists"] = [coord_list.text 
                                 for coord_list in regular_grid.findall(ns_rep("coordList"))]
        
        return data.RegularGridBrowse(**kwargs)
        
    elif model_in_geotiff is not None:
        logger.info("Parsing GeoTIFF Browse.")
        return data.ModelInGeotiffBrowse(**kwargs)
    
    elif vertical_curtain_footprint is not None:
        logger.info("Parsing Vertical Curtain Browse.")
        return data.VerticalCurtainBrowse(**kwargs)
    
    else:
        raise ParsingException("Missing geo-spatial reference type.")


def parse_coord_list(coord_list, swap_axes=False):
    if not swap_axes:
        return list(pairwise(map(float, coord_list.split())))
    else:
        coords = list(pairwise(map(float, coord_list.split())))
        return [(y, x) for (x, y) in coords]
