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

from os.path import exists
import sqlite3


URN_TO_GRID = {
    "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible": "GoogleMapsCompatible",
    "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad": "WGS84"
}


class TileSetException(Exception):
    pass


def open(path):
    if not exists:
        raise TileSetException("TileSet '%s' does not exist.")
    return TileSet(path)


class TileSet(object):
    def __init__(self, path):
        self.path = path
            
    def get_tiles(self, tileset, grid, dim=None, minzoom=None, maxzoom=None):
        with sqlite3.connect(self.path) as connection:
            cur = connection.cursor()
            where_clauses = [
                "tiles.grid = '%s'" % grid,
                "tiles.tileset = '%s'" % tileset
            ]
            
            # TODO: make this work properly
            """
            if self.begin_time:
                where_clauses.append("ctime >= datetime('%s')"
                                     % self.begin_time)#.isoformat("T"))
            
            if self.begin_time:
                where_clauses.append("ctime >= datetime('%s')"
                                     % self.begin_time)#.isoformat("T"))
            
            if self.end_time:
                where_clauses.append("ctime <= datetime('%s')"
                                     % self.end_time)#.isoformat("T"))
            """
            
            if minzoom is not None:
                where_clauses.append("tiles.z >= %d" % minzoom)
            
            if maxzoom is not None:
                where_clauses.append("tiles.z <= %d" % maxzoom)
            
            #rows = self.rows or "tileset, grid, x, y, z, dim, data"
            
            sql = ("SELECT tileset, grid, x, y, z, dim, data FROM tiles%s;" 
                   % (" WHERE " + " AND ".join(where_clauses) 
                      if len(where_clauses) else ""))
            
            print sql
            
            cur.execute(sql)
            
            while True:
                row = cur.fetchone()
                if not row:
                    break
                
                yield row 
        
