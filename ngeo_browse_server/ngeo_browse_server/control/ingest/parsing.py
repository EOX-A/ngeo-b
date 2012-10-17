from itertools import izip

from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.config.models import (
    BrowseReport, BrowseIdentifier, RectifiedBrowse, FootprintBrowse,
    RegularGridBrowse, VerticalCurtainBrowse, ModelInGeotiffBrowse,
    RegularGridCoordList
)  


def ns_rep(tag):
    "Namespacify a given tag name for the use with etree"
    return "{http://ngeo.eo.esa.int/schema/browseReport}" + tag


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


def parse_browse_report(browse_report):
    """ Parsing function to return a BrowseReport object from an 
        ElementTree.Element node.
    """
    
    date_time = getDateTime(browse_report.find(ns_rep("dateTime")).text)
    #browse_type = browse_report.find(ns_rep("browseType")).text
    responsible_org_name = browse_report.find(ns_rep("responsibleOrgName")).text
    
    #browses = [parse_browse(browse) 
    #           for browse in browse_report.iter(ns_rep("browse"))]

    report = BrowseReport(#browse_type=browse_type,
                          date_time=date_time,
                          responsible_org_name=responsible_org_name)
    
    for browse in browse_report.iter(ns_rep("browse")):
        parse_browse(browse, report)


def parse_browse(browse, browse_report=None):
    """ Parsing function to return a Browse object from an ElementTree.Element
        node.
    """
    kwargs = {
        "file_name": browse.find(ns_rep("fileName")).text,
        "image_type": browse.find(ns_rep("imageType")).text,
        "reference_system_identifier": browse.find(ns_rep("referenceSystemIdentifier")).text,
        "start_time": getDateTime(browse.find(ns_rep("startTime")).text),
        "end_time": getDateTime(browse.find(ns_rep("endTime")).text),
    }
    
    browse_identifier = browse.find(ns_rep("browseIdentifier"))
    if browse_identifier is not None:
        kwargs["browse_identifier"] = BrowseIdentifier(id=browse_identifier.text)
    
    
    rectified_browse = browse.find(ns_rep("rectifiedBrowse"))
    footprint = browse.find(ns_rep("footprint"))
    regular_grid = browse.find(ns_rep("regularGrid"))
    model_in_geotiff = browse.find(ns_rep("modelInGeotiff"))
    vertical_curtain_footprint = browse.find(ns_rep("verticalCurtainFootprint"))
    
    if rectified_browse is not None:
        (minx, miny), (maxx, maxy) = parse_coord_list(footprint.find(ns_rep("coordList")))
        return RectifiedBrowse(minx=minx, miny=miny, maxx=maxx, maxy=maxy, **kwargs)
    
    elif footprint is not None:
        kwargs["node_number"] = int(footprint.attr["nodeNumber"])
        kwargs["col_row_list"] = footprint.find(ns_rep("colRowList")).text
        kwargs["coord_list"] = footprint.find(ns_rep("coordList")).text
        
        return FootprintBrowse(**kwargs)
    
    elif regular_grid is not None:
        kwargs["col_node_number"] = int(regular_grid.find(ns_rep("colNodeNumber")).text)
        kwargs["row_node_number"] = int(regular_grid.find(ns_rep("rowNodeNumber")).text)
        kwargs["col_step"] = float(regular_grid.find(ns_rep("colStep")).text)
        kwargs["row_step"] = float(regular_grid.find(ns_rep("rowStep")).text)
        
        
        browse = RegularGridBrowse(**kwargs)
        
        for coord_list in regular_grid.findall(ns_rep("coordList")):
            RegularGridCoordList(regular_grid_browse=browse, coord_list=coord_list.text)
        
        return browse
    
       
    
    elif model_in_geotiff is not None:
        return ModelInGeotiffBrowse(**kwargs)
    
    elif vertical_curtain_footprint is not None:
        VerticalCurtainBrowse
        # TODO
        raise NotImplementedError

    raise ValueError


def parse_coord_list(coord_list):
    return list(pairwise(map(float, coord_list.text.split())))

"""
class Browse(object):
    def __init__(self, browse_id, browse_file, srid, start_time, end_time, 
                 extent=None, gcps=None):
        self._browse_id = browse_id
        self._browse_file = browse_file
        self._srid = srid
        self._start_time = start_time
        self._end_time = end_time
        self._extent = extent
        self._gcps = gcps
    
    browse_id = property(lambda self: self._browse_id)
    browse_file = property(lambda self: self._browse_file)
    srid = property(lambda self: self._srid)
    start_time = property(lambda self: self._start_time)
    end_time = property(lambda self: self._end_time)
    extent = property(lambda self: self._extent)
    gcps = property(lambda self: self._gcps)


class BrowseReport(object):
    def __init__(self, browse_type, date_time, responsible_org, browses):
        self._browse_type = browse_type
        self._date_time = date_time
        self._responsible_org = responsible_org
        self._browses = browses
    
    
    def __iter__(self):
        return iter(self._browses)
    
    
    browse_type = property(lambda self: self._browse_type)
    date_time = property(lambda self: self._date_time)
    responsible_org = property(lambda self: self._responsible_org)
        
"""


