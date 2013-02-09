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

from ngeo_browse_server.namespace import ns_cfg
from ngeo_browse_server.config.browselayer.data import BrowseLayer


logger = logging.getLogger(__name__)


def parse_browse_layers(browse_layers_elem):
    logger.info("Start parsing browse layer.")
    
    #TODO: browse_layers_elem.tag == ns_cfg("browseLayers")
    
    browse_layers = []
    for browse_layer_elem in browse_layers_elem.findall(ns_cfg("browseLayer")):
    
        opt = {}
        description_elem = browse_layer_elem.find(ns_cfg("description"))
        if description_elem is not None:
            opt["description"] = description_elem.text
        
        related_dataset_ids_elem = browse_layer_elem.find(ns_cfg("relatedDatasetIds"))
        related_dataset_ids = [elem.text for elem in related_dataset_ids_elem]
        
        rgb_bands_elem = browse_layer_elem.find(ns_cfg("rgbBands"))
        if rgb_bands_elem is not None:
            r, g, b = map(int, rgb_bands_elem.text.split(","))
            opt["r_band"] = r; opt["g_band"] = g; opt["b_band"] = b
        
        radiometric_interval_elem = browse_layer_elem.find(ns_cfg("radiometricInterval"))
        if radiometric_interval_elem is not None:
            opt["radiometric_interval_min"] = int(radiometric_interval_elem.find(ns_cfg("min")).text)
            opt["radiometric_interval_max"] = int(radiometric_interval_elem.find(ns_cfg("max")).text)
        
        browse_layers.append(BrowseLayer(
            browse_layer_elem.get("browseLayerId"),
            browse_layer_elem.find(ns_cfg("browseType")).text,
            browse_layer_elem.find(ns_cfg("title")).text,
            browse_layer_elem.find(ns_cfg("grid")).text,
            browse_layer_elem.find(ns_cfg("browseAccessPolicy")).text,
            browse_layer_elem.find(ns_cfg("containsVerticalCurtains")).text == "true",
            int(browse_layer_elem.find(ns_cfg("highestMapLevel")).text),
            int(browse_layer_elem.find(ns_cfg("lowestMapLevel")).text),
            browse_layer_elem.find(ns_cfg("hostingBrowseServerName")).text,
            related_dataset_ids,
            **opt
        ))
    
    return browse_layers
