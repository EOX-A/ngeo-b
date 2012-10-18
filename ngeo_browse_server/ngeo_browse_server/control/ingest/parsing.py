from itertools import izip

from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.config.models import (
    BrowseReport, BrowseIdentifier, RectifiedBrowse, FootprintBrowse,
    RegularGridBrowse, VerticalCurtainBrowse, ModelInGeotiffBrowse,
    RegularGridCoordList
, BrowseType)  


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
    
    return ParsedBrowseReport(
        date_time=getDateTime(browse_report.find(ns_rep("dateTime")).text),
        browse_type=browse_report.find(ns_rep("browseType")).text,
        responsible_org_name=browse_report.find(ns_rep("responsibleOrgName")).text,
        browses=[parse_browse(browse_elem)
                 for browse_elem in browse_report.iter(ns_rep("browse"))]
    )
    
    """
    date_time = getDateTime(browse_report.find(ns_rep("dateTime")).text)
    browse_type_txt = browse_report.find(ns_rep("browseType")).text
    responsible_org_name = browse_report.find(ns_rep("responsibleOrgName")).text
    
    #browses = [parse_browse(browse) 
    #           for browse in browse_report.iter(ns_rep("browse"))]

    browse_type, _ = BrowseType.objects.get_or_create(id=browse_type_txt)
    report = BrowseReport(browse_type=browse_type,
                          date_time=date_time,
                          responsible_org_name=responsible_org_name)
    
    report.save()
    
    browses = [parse_browse(browse_elem, report) for browse_elem in browse_report.iter(ns_rep("browse"))]
        
    return report, browses
    """


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
        extent = parse_coord_list(footprint.find(ns_rep("coordList")))
        return ParsedRectifiedBrowse(*extent, **kwargs)
    
    elif footprint is not None:
        kwargs["node_number"] = int(footprint.attr["nodeNumber"])
        kwargs["col_row_list"] = footprint.find(ns_rep("colRowList")).text
        kwargs["coord_list"] = footprint.find(ns_rep("coordList")).text
        
        return ParsedFootprintBrowse(**kwargs)
    
    elif regular_grid is not None:
        kwargs["col_node_number"] = int(regular_grid.find(ns_rep("colNodeNumber")).text)
        kwargs["row_node_number"] = int(regular_grid.find(ns_rep("rowNodeNumber")).text)
        kwargs["col_step"] = float(regular_grid.find(ns_rep("colStep")).text)
        kwargs["row_step"] = float(regular_grid.find(ns_rep("rowStep")).text)
        kwargs["coord_lists"] = [coord_list.text 
                                 for coord_list in regular_grid.findall(ns_rep("coordList"))]
        
        return ParsedRegularGridBrowse(**kwargs)
        
    elif model_in_geotiff is not None:
        return ParsedModelInGeotiffBrowse(**kwargs)
    
    elif vertical_curtain_footprint is not None:
        return ParsedVerticalCurtainBrowse(**kwargs)
    
    """
    kwargs = {
        "browse_report": browse_report,
        "file_name": browse_elem.find(ns_rep("fileName")).text,
        "image_type": browse_elem.find(ns_rep("imageType")).text,
        "reference_system_identifier": browse_elem.find(ns_rep("referenceSystemIdentifier")).text,
        "start_time": getDateTime(browse_elem.find(ns_rep("startTime")).text),
        "end_time": getDateTime(browse_elem.find(ns_rep("endTime")).text),
    }
    
    # check type of geo reference
    rectified_browse = browse_elem.find(ns_rep("rectifiedBrowse"))
    footprint = browse_elem.find(ns_rep("footprint"))
    regular_grid = browse_elem.find(ns_rep("regularGrid"))
    model_in_geotiff = browse_elem.find(ns_rep("modelInGeotiff"))
    vertical_curtain_footprint = browse_elem.find(ns_rep("verticalCurtainFootprint"))
    
    if rectified_browse is not None:
        (minx, miny), (maxx, maxy) = parse_coord_list(footprint.find(ns_rep("coordList")))
        browse = RectifiedBrowse(minx=minx, miny=miny, maxx=maxx, maxy=maxy, **kwargs)
    
    elif footprint is not None:
        kwargs["node_number"] = int(footprint.attr["nodeNumber"])
        kwargs["col_row_list"] = footprint.find(ns_rep("colRowList")).text
        kwargs["coord_list"] = footprint.find(ns_rep("coordList")).text
        
        browse = FootprintBrowse(**kwargs)
    
    elif regular_grid is not None:
        kwargs["col_node_number"] = int(regular_grid.find(ns_rep("colNodeNumber")).text)
        kwargs["row_node_number"] = int(regular_grid.find(ns_rep("rowNodeNumber")).text)
        kwargs["col_step"] = float(regular_grid.find(ns_rep("colStep")).text)
        kwargs["row_step"] = float(regular_grid.find(ns_rep("rowStep")).text)
        
        browse = RegularGridBrowse(**kwargs)
        browse.save()
        
        # add coord lists for each row
        for coord_list in regular_grid.findall(ns_rep("coordList")):
            browse.coord_lists.add(RegularGridCoordList(regular_grid_browse=browse, coord_list=coord_list.text))
    
    elif model_in_geotiff is not None:
        browse = ModelInGeotiffBrowse(**kwargs)
    
    elif vertical_curtain_footprint is not None:
        browse = VerticalCurtainBrowse()
        raise NotImplementedError
    
    # check if an identifier was specified
    browse_identifier = browse_elem.find(ns_rep("browseIdentifier"))
    if browse_identifier is not None:
        BrowseIdentifier.objects.create(id=browse_identifier.text, browse=browse)
    
    return browse
    """


def parse_coord_list(coord_list, swap_axes=False):
    if not swap_axes:
        return list(pairwise(map(float, coord_list.split())))
    else:
        coords = list(pairwise(map(float, coord_list.split())))
        return [(y, x) for (x, y) in coords]
        


# TODO: in the parsing module don't actually use the models

#===============================================================================
# Parse results
#===============================================================================

class ParsedBrowse(object):

    def __init__(self, browse_identifier, file_name, image_type,
                 reference_system_identifier, start_time, end_time,):
        self._browse_id = browse_identifier
        self._file_name = file_name
        self._image_type = image_type
        self._reference_system_identifier = reference_system_identifier
        self._start_time = start_time
        self._end_time = end_time


    browse_identifier = property(lambda self: self._browse_identifier)
    file_name = property(lambda self: self._file_name)
    image_type = property(lambda self: self._image_type)
    reference_system_identifier = property(lambda self: self._reference_system_identifier)
    start_time = property(lambda self: self._start_time)
    end_time = property(lambda self: self._end_time)


    def get_kwargs(self):
        return {
            "file_name": self.file_name,
            "image_type": self.image_type,
            "reference_system_identifier": self.reference_system_identifier,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

    
class ParsedRectifiedBrowse(ParsedBrowse):
    
    def __init__(self, minx, miny, maxx, maxy, *args, **kwargs):
        super(ParsedRectifiedBrowse, self).__init__(*args, **kwargs)
        self._extent = minx, miny, maxx, maxy
    
    minx = property(lambda self: self._extent[0])
    miny = property(lambda self: self._extent[1])
    maxx = property(lambda self: self._extent[2])
    maxy = property(lambda self: self._extent[3])


    def get_kwargs(self):
        kwargs = super(ParsedRectifiedBrowse, self).get_kwargs()
        kwargs.update({
            "minx": self.minx,
            "miny": self.miny,
            "maxx": self.maxx,
            "maxy": self.maxy
        })
        return kwargs

class ParsedFootprintBrowse(ParsedBrowse):
    
    def __init__(self, node_number, col_row_list, coord_list, *args, **kwargs):
        super(ParsedFootprintBrowse, self).__init__(*args, **kwargs)
        self._node_number = node_number
        self._col_row_list = col_row_list
        self._coord_list = coord_list


    node_number = property(lambda self: self._node_number)
    col_row_list = property(lambda self: self._col_row_list)
    coord_list = property(lambda self: self._coord_list)
    
    
    def get_kwargs(self):
        kwargs = super(ParsedFootprintBrowse, self).get_kwargs()
        kwargs.update({
            "node_number": self._node_number,
            "col_row_list": self._col_row_list,
            "coord_list": self._coord_list
        })
        return kwargs


class ParsedRegularGridBrowse(ParsedBrowse):
    
    def __init__(self, col_node_number, row_node_number, col_step, row_step, 
                 coord_lists, *args, **kwargs):
        
        super(ParsedRegularGridBrowse, self).__init__(*args, **kwargs)
        
        self._col_node_number = col_node_number
        self._row_node_number = row_node_number
        self._col_step = col_step
        self._row_step = row_step
        self._coord_lists = coord_lists

    col_node_number = property(lambda self: self._col_node_number)
    row_node_number = property(lambda self: self._row_node_number)
    col_step = property(lambda self: self._col_step)
    row_step = property(lambda self: self._row_step)
    coord_lists = property(lambda self: self._coord_lists)
    
    def get_kwargs(self):
        kwargs = super(ParsedRegularGridBrowse, self).get_kwargs()
        kwargs.update({
            "col_node_number": self._col_node_number,
            "row_node_number": self._row_node_number,
            "col_step": self._col_step,
            "row_step": self._row_step
        })
        return kwargs

    
class ParsedVerticalCurtainBrowse(ParsedBrowse):
    pass


class ParsedModelInGeotiffBrowse(ParsedBrowse):
    pass


class ParsedBrowseReport(object):
    
    def __init__(self, browse_type, date_time, responsible_org_name, browses):
        self._browse_type = browse_type
        self._date_time = date_time
        self._responsible_org_name = responsible_org_name
        self._browses = list(browses)
    
    
    def __iter__(self):
        return iter(self._browses)
    
    
    def append(self, browse):
        self._browses.append(browse)
    
    
    browse_type = property(lambda self: self._browse_type)
    date_time = property(lambda self: self._date_time)
    responsible_org_name = property(lambda self: self._responsible_org_name)
    
    def get_kwargs(self):
        return {
            "date_time": self._date_time,
            "responsible_org_name": self._responsible_org_name
        }
