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


from lxml import etree
from ngeo_browse_server.control.namespace import ns_cfg

def serialize_browse_layers(browse_layers, stream, pretty_print=False):
    browse_layers_elem = etree.Element(ns_cfg("browseLayers"),
                                       nsmap={"cfg": ns_cfg("")})
    
    for browse_layer in browse_layers:
        bl_elem = etree.SubElement(
            browse_layers_elem, ns_cfg("browseLayer"), 
            attrib={"browseLayerId": browse_layer.browse_layer_identifier}
        )
        
        rgb = browse_layer.r_band, browse_layer.g_band, browse_layer.b_band
        has_rgb = len(filter(lambda v: v is not None, rgb)) == 3
        
        ri = browse_layer.radiometric_interval_min, browse_layer.radiometric_interval_max
        has_ri = len(filter(lambda v: v is not None, ri)) == 2 
        
        etree.SubElement(bl_elem, ns_cfg("browseType")).text = browse_layer.browse_type
        etree.SubElement(bl_elem, ns_cfg("title")).text = browse_layer.title
        if browse_layer.description is not None:
            etree.SubElement(bl_elem, ns_cfg("description")).text = browse_layer.description
        etree.SubElement(bl_elem, ns_cfg("browseAccessPolicy")).text = browse_layer.browse_access_policy
        etree.SubElement(bl_elem, ns_cfg("hostingBrowseServerName")).text = ""
        etree.SubElement(bl_elem, ns_cfg("relatedDatasetIds")) # TODO
        etree.SubElement(bl_elem, ns_cfg("containsVerticalCurtains")).text = "true" if browse_layer.contains_vertical_curtains else "false"
        if has_rgb:
            etree.SubElement(bl_elem, ns_cfg("rgbBands")).text = ",".join(map(str, rgb))
        
        if has_ri:
            ri_elem = etree.SubElement(bl_elem, ns_cfg("radiometricInterval"))
            etree.SubElement(ri_elem, ns_cfg("min")).text = str(ri[0])
            etree.SubElement(ri_elem, ns_cfg("max")).text = str(ri[1])
        
        etree.SubElement(bl_elem, ns_cfg("highestMapLevel")).text = str(browse_layer.highest_map_level)
        etree.SubElement(bl_elem, ns_cfg("lowestMapLevel")).text = str(browse_layer.lowest_map_level)
    
    # TODO: encoding
    browse_layers_elem.write(file, pretty_print=pretty_print)
