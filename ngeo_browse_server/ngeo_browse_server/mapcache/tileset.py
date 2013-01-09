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

import sqlite3


URN_TO_GRID = {
    "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible": "GoogleMapsCompatible",
    "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad": "WGS84"
}


class TileSet(object):
    def __init__(self, path, grid=None, tileset=None, begin_time=None,
                 end_time=None, minx=None, miny=None, maxx=None, maxy=None,
                 min_zoom=None, max_zoom=None, rows=None):
        self.path = path
        self.grid = grid
        self.tileset = tileset
        self.begin_time = begin_time
        self.end_time = end_time
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.rows = rows
    
            
    def __iter__(self):
        with sqlite3.connect(self.path) as connection:
            cur = connection.cursor()
            where_clauses = []
            
            if self.grid:
                where_clauses.append("tiles.grid = '%s'" % self.grid)
            
            if self.tileset:
                where_clauses.append("tiles.tileset = '%s'" % self.tileset)
            
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
            
            
            # TODO: translate bbox to x/y values
            
            if self.minx is not None:
                where_clauses.append("tiles.x >= %f" % self.minx)
            
            if self.miny is not None:
                where_clauses.append("tiles.y >= %f" % self.miny)
            
            if self.maxx is not None:
                where_clauses.append("tiles.x <= %f" % self.maxx)
            
            if self.maxy is not None:
                where_clauses.append("tiles.y <= %f" % self.maxy)
            
            if self.min_zoom is not None:
                where_clauses.append("tiles.z >= %d" % self.min_zoom)
            
            if self.max_zoom is not None:
                where_clauses.append("tiles.z <= %d" % self.max_zoom)
            
            rows = self.rows or "tileset, grid, x, y, z, dim, data"
            
            sql = ("SELECT %s FROM tiles%s;" 
                   % (rows, (" WHERE " + " AND ".join(where_clauses) 
                             if len(where_clauses) else "")))
            
            print sql
            
            cur.execute(sql)
            
            while True:
                row = cur.fetchone()
                if not row:
                    break
                
                yield row 
        
