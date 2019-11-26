#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 European Space Agency
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

from ngeo_browse_server.namespace import ns_cfg


def serialize_browse_layers(browse_layers, stream=None, pretty_print=False):
    if not stream:
        stream = StringIO()
    browse_layers_elem = Element(ns_cfg("browseLayers"), 
                                 nsmap={"cfg": ns_cfg.uri})
    
    for browse_layer in browse_layers:
        bl_elem = SubElement(
            browse_layers_elem, ns_cfg("browseLayer"), 
            attrib={"browseLayerId": browse_layer.id}
        )
        
        rgb = browse_layer.r_band, browse_layer.g_band, browse_layer.b_band
        has_rgb = len(filter(lambda v: v is not None, rgb)) == 3
        
        ri = browse_layer.radiometric_interval_min, browse_layer.radiometric_interval_max
        has_ri = len(filter(lambda v: v is not None, ri)) == 2 
        
        SubElement(bl_elem, ns_cfg("browseType")).text = browse_layer.browse_type
        SubElement(bl_elem, ns_cfg("title")).text = browse_layer.title
        if browse_layer.description is not None:
            SubElement(bl_elem, ns_cfg("description")).text = browse_layer.description
        SubElement(bl_elem, ns_cfg("grid")).text = browse_layer.grid
        SubElement(bl_elem, ns_cfg("browseAccessPolicy")).text = browse_layer.browse_access_policy
        SubElement(bl_elem, ns_cfg("hostingBrowseServerName")).text = ""
        rel_ds_elem = SubElement(bl_elem, ns_cfg("relatedDatasetIds"))
        for rel_ds_id in browse_layer.related_dataset_ids:
            SubElement(rel_ds_elem, ns_cfg("datasetId")).text = rel_ds_id
        SubElement(bl_elem, ns_cfg("containsVerticalCurtains")).text = "true" if browse_layer.contains_vertical_curtains else "false"
        SubElement(bl_elem, ns_cfg("shortenIngestedInterval")).text = str(browse_layer.shorten_ingested_interval)
        if has_rgb:
            SubElement(bl_elem, ns_cfg("rgbBands")).text = ",".join(map(str, rgb))
        
        if has_ri:
            ri_elem = SubElement(bl_elem, ns_cfg("radiometricInterval"))
            SubElement(ri_elem, ns_cfg("min")).text = str(ri[0])
            SubElement(ri_elem, ns_cfg("max")).text = str(ri[1])
        
        SubElement(bl_elem, ns_cfg("highestMapLevel")).text = str(browse_layer.highest_map_level)
        SubElement(bl_elem, ns_cfg("lowestMapLevel")).text = str(browse_layer.lowest_map_level)
        SubElement(bl_elem, ns_cfg("timeDimensionDefault")).text = str(browse_layer.timedimension_default)
        SubElement(bl_elem, ns_cfg("tileQueryLimit")).text = str(browse_layer.tile_query_limit)
    
    # TODO: encoding
    et = ElementTree(browse_layers_elem)
    et.write(stream, pretty_print=pretty_print, encoding="utf-8", 
             xml_declaration=True)
    
    return stream
