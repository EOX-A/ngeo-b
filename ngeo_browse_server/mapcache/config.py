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

from os.path import join

from ngeo_browse_server.config import get_ngeo_config, safe_get, get_project_relative_path


MAPCACHE_SECTION = "mapcache"
SEED_SECTION = "mapcache.seed"


def get_mapcache_seed_config(config=None):
    """ Returns a dicitonary with all mapcache related config settings. """
    
    values = {}
    config = config or get_ngeo_config()
    
    values["seed_command"] = safe_get(config, SEED_SECTION, "seed_command", "mapcache_seed")
    values["config_file"] = config.get(SEED_SECTION, "config_file")
    values["threads"] = int(safe_get(config, SEED_SECTION, "threads", 1))
    
    return values


def get_tileset_path(browse_type, config=None):
    """ Returns the path to a tileset SQLite file in the `tileset_root` dir. """
    
    config = config or get_ngeo_config()
    
    tileset_root = config.get(MAPCACHE_SECTION, "tileset_root")
    tileset = browse_type + ".sqlite" if not browse_type.endswith(".sqlite") else ""
    
    return join(get_project_relative_path(tileset_root), tileset)
