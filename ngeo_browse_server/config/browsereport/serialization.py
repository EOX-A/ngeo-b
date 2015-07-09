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


from cStringIO import StringIO

from lxml.etree import Element, SubElement, ElementTree

from ngeo_browse_server.namespace import ns_rep


def serialize_browse_report(browse_report, stream=None, pretty_print=False):
    if not stream:
        stream = StringIO()

    browse_report_elem = Element(ns_rep("browseReport"),
                                 nsmap={"rep": ns_rep.uri},
                                 attrib={"version": "1.3"})

    SubElement(browse_report_elem, ns_rep("responsibleOrgName")).text = browse_report.responsible_org_name
    SubElement(browse_report_elem, ns_rep("dateTime")).text = browse_report.date_time.isoformat("T")
    SubElement(browse_report_elem, ns_rep("browseType")).text = browse_report.browse_type

    for browse in browse_report:
        browse_report_elem.append(_serialize_browse(browse))

    et = ElementTree(browse_report_elem)
    et.write(stream, pretty_print=pretty_print, encoding="utf-8",
             xml_declaration=True)

    return stream


def _serialize_browse(browse):
    browse_elem = Element(ns_rep("browse"))
    if browse.browse_identifier:
        SubElement(browse_elem, ns_rep("browseIdentifier")).text = browse.browse_identifier
    SubElement(browse_elem, ns_rep("fileName")).text = browse.file_name
    SubElement(browse_elem, ns_rep("imageType")).text = browse.image_type
    SubElement(browse_elem, ns_rep("referenceSystemIdentifier")).text = browse.reference_system_identifier

    browse_elem.append(GEO_TYPE_TO_XML[browse.geo_type](browse))

    SubElement(browse_elem, ns_rep("startTime")).text = browse.start_time.isoformat("T")
    SubElement(browse_elem, ns_rep("endTime")).text = browse.end_time.isoformat("T")
    return browse_elem


def _serialize_rectified_browse(browse):
    georef_elem = Element(ns_rep("rectifiedBrowse"))
    SubElement(georef_elem, ns_rep("coordList")).text = browse.coord_list
    return georef_elem

def _serialize_footprint_browse(browse):
    georef_elem = Element(ns_rep("footprint"), attrib={"nodeNumber": str(browse.node_number)})
    SubElement(georef_elem, ns_rep("colRowList")).text = browse.col_row_list
    SubElement(georef_elem, ns_rep("coordList")).text = browse.coord_list
    return georef_elem

def _serialize_regular_grid_browse(browse):
    georef_elem = Element(ns_rep("regularGrid"))
    SubElement(georef_elem, ns_rep("colNodeNumber")).text = str(browse.col_node_number)
    SubElement(georef_elem, ns_rep("rowNodeNumber")).text = str(browse.row_node_number)
    SubElement(georef_elem, ns_rep("colStep")).text = str(browse.col_step)
    SubElement(georef_elem, ns_rep("rowStep")).text = str(browse.row_step)
    for coord_list in browse.coord_lists:
        SubElement(georef_elem, ns_rep("coordList")).text = coord_list
    return georef_elem


def _serialize_model_in_geotiff_browse(browse):
    georef_elem = Element(ns_rep("modelInGeotiff"))
    georef_elem.text = "true"
    return georef_elem


GEO_TYPE_TO_XML = {
    "rectifiedBrowse": _serialize_rectified_browse,
    "footprintBrowse": _serialize_footprint_browse,
    "regularGridBrowse": _serialize_regular_grid_browse,
    "modelInGeotiffBrowse": _serialize_model_in_geotiff_browse
}
