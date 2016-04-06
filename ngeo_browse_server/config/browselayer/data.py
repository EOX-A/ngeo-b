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


class BrowseLayer(object):
    def __init__(self, browse_layer_identifier, browse_type, title, grid,
                 browse_access_policy, contains_vertical_curtains, 
                 highest_map_level, lowest_map_level, 
                 hosting_browse_server_name, related_dataset_ids,
                 description="", r_band=None, g_band=None, b_band=None,
                 radiometric_interval_min=None, radiometric_interval_max=None,
                 strategy=None, timedimension_default=None, 
                 tile_query_limit=None):
        self._browse_layer_identifier = browse_layer_identifier
        self._browse_type = browse_type
        self._title = title
        self._description = description
        self._grid = grid
        self._browse_access_policy = browse_access_policy
        self._hosting_browse_server_name = hosting_browse_server_name
        self._related_dataset_ids = related_dataset_ids
        self._contains_vertical_curtains = contains_vertical_curtains
        self._r_band = r_band
        self._g_band = g_band
        self._b_band = b_band
        self._radiometric_interval_min = radiometric_interval_min
        self._radiometric_interval_max = radiometric_interval_max
        self._highest_map_level = highest_map_level
        self._lowest_map_level = lowest_map_level
        self._strategy = strategy
        self._timedimension_default = timedimension_default
        self._tile_query_limit = tile_query_limit
    
    id = property(lambda self: self._browse_layer_identifier)
    browse_type = property(lambda self: self._browse_type)
    title = property(lambda self: self._title)
    description = property(lambda self: self._description)
    grid = property(lambda self: self._grid)
    browse_access_policy = property(lambda self: self._browse_access_policy)
    hosting_browse_server_name = property(lambda self: self._hosting_browse_server_name)
    related_dataset_ids = property(lambda self: self._related_dataset_ids)
    contains_vertical_curtains = property(lambda self: self._contains_vertical_curtains)
    r_band = property(lambda self: self._r_band)
    g_band = property(lambda self: self._g_band)
    b_band = property(lambda self: self._b_band)
    radiometric_interval_min = property(lambda self: self._radiometric_interval_min)
    radiometric_interval_max = property(lambda self: self._radiometric_interval_max)
    highest_map_level = property(lambda self: self._highest_map_level)
    lowest_map_level = property(lambda self: self._lowest_map_level)
    strategy = property(lambda self: self._strategy)
    timedimension_default = property(lambda self: self._timedimension_default)
    tile_query_limit = property(lambda self: self._tile_query_limit)

    
    def get_kwargs(self):
        return {
            "id": self.id,
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
            "lowest_map_level": self.lowest_map_level,
            "strategy": self.strategy,
            "timedimension_default": self.timedimension_default,
            "tile_query_limit": self.tile_query_limit
        }

    @classmethod
    def from_model(cls, model):
        return cls(
            browse_layer_identifier=model.id, browse_type=model.browse_type,
            title=model.title, description=model.description, grid=model.grid, 
            browse_access_policy=model.browse_access_policy,
            hosting_browse_server_name="",
            related_dataset_ids=[rel_ds.dataset_id 
                                 for rel_ds in model.related_datasets.all()],
            contains_vertical_curtains=model.contains_vertical_curtains,
            r_band=model.r_band, g_band=model.g_band, b_band=model.b_band,
            radiometric_interval_min=model.radiometric_interval_min,
            radiometric_interval_max=model.radiometric_interval_max,
            highest_map_level=model.highest_map_level,
            lowest_map_level=model.lowest_map_level,
            timedimension_default=model.timedimension_default,
            tile_query_limit=model.tile_query_limit
        )
