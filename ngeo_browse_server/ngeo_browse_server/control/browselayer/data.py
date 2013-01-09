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


class BrowseLayer(object):
    def __init__(self, browse_layer_identifier, browse_type, title, grid,
                 browse_access_policy, contains_vertical_curtains, 
                 highest_map_level, lowest_map_level,
                 description=None, r_band=None, g_band=None, b_band=None,
                 radiometric_interval_min=None, radiometric_interval_max=None):
        self._browse_layer_identifier = browse_layer_identifier
        self._browse_type = browse_type
        self._title = title
        self._description = description
        self._grid = grid
        self._browse_access_policy = browse_access_policy
        self._contains_vertical_curtains = contains_vertical_curtains
        self._r_band = r_band
        self._g_band = g_band
        self._b_band = b_band
        self._radiometric_interval_min = radiometric_interval_min
        self._radiometric_interval_max = radiometric_interval_max
        self._highest_map_level = highest_map_level
        self._lowest_map_level = lowest_map_level
    
    browse_layer_identifier = property(lambda self: self._browse_layer_identifier)
    browse_type = property(lambda self: self._browse_type)
    title = property(lambda self: self._title)
    description = property(lambda self: self._description)
    grid = property(lambda self: self._grid)
    browse_access_policy = property(lambda self: self._browse_access_policy)
    contains_vertical_curtains = property(lambda self: self._contains_vertical_curtains)
    r_band = property(lambda self: self._r_band)
    g_band = property(lambda self: self._g_band)
    b_band = property(lambda self: self._b_band)
    radiometric_interval_min = property(lambda self: self._radiometric_interval_min)
    radiometric_interval_max = property(lambda self: self._radiometric_interval_max)
    highest_map_level = property(lambda self: self._highest_map_level)
    lowest_map_level = property(lambda self: self._lowest_map_level)
    
    def get_kwargs(self):
        return {
            "id": self.browse_layer_identifier,
            "browse_type": self.browse_type,
            "title": self.title,
            "description": self.description,
            "grid": self.grid,
            "browse_access_policy": self.browse_access_policy,
            "contains_vertical_curtains": self.contains_vertical_curtains,
            "r_band": self.r_band,
            "g_band": self.g_band,
            "b_band": self.b_band,
            "radiometric_interval_min": self.radiometric_interval_min,
            "radiometric_interval_max": self.radiometric_interval_max,
            "highest_map_level": self.highest_map_level,
            "lowest_map_level": self.lowest_map_level
        }
        
