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

from os.path import exists, basename, isfile
import sqlite3
from io import BytesIO
from datetime import datetime

from django.db import models, connections


URN_TO_GRID = {
    "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible": "GoogleMapsCompatible",
    "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad": "WGS84"
}

# Django does not support multi-column primary keys
class TileModel(models.Model):
    tileset = models.TextField()
    grid = models.TextField()
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    data = models.TextField() # TODO: wrapper for blob
    dim = models.TextField()
    ctime = models.DateTimeField()
    
    class Meta(object):
        db_table = "tiles"


def open_queryset(path):
    if not exists(path):
        raise TileSetException("TileSet '%s' does not exist.")
    
    name = basename(path)
    if not name in connections.databases:        
        connections.databases[name] = {
            "NAME": path,
            "ENGINE": "django.db.backends.sqlite3"
        }
        
    _ = connections[name]
    
    return TileModel.objects.using(name)

# end TODO

class TileSetException(Exception):
    pass


def open(path, mode="r"):
    db_exists = isfile(path)
    create = False
    if not db_exists and mode == "r":
        raise TileSetException("TileSet '%s' does not exist." % path)
    elif not db_exists and mode == "w":
        create = True
    
    # TODO: schema detection
    # SELECT name FROM sqlite_master WHERE type = 'table';
    # TODO: other schemas
    return SQLiteSchemaTileSet(path, create)


class SQLiteSchemaTileSet(object):
    def __init__(self, path, create=False):
        self.path = path
        
        if create:
            with sqlite3.connect(path) as connection:
                cur = connection.cursor()
                cur.executescript("""\
                    create table if not exists tiles(
                        tileset text,
                        grid text,
                        x integer,
                        y integer,
                        z integer,
                        data blob,
                        dim text,
                        ctime datetime,
                        primary key(tileset,grid,x,y,z,dim)
                    );
                """)
            
    def get_tiles(self, tileset, grid, dim=None, minzoom=None, maxzoom=None):
        """ Generator function to loop over all tiles in a given zoom interval
        and a given dimension.
        """
        with sqlite3.connect(self.path) as connection:
            cur = connection.cursor()
            where_clauses = [
                "tiles.grid = '%s'" % grid,
                "tiles.tileset = '%s'" % tileset
            ]
            
            if minzoom is not None:
                where_clauses.append("tiles.z <= %d" % minzoom)
            
            if maxzoom is not None:
                where_clauses.append("tiles.z >= %d" % maxzoom)
                
            if dim:
                where_clauses.append("tiles.dim = '%s'" % dim)
            
            #rows = self.rows or "tileset, grid, x, y, z, dim, data"
            
            sql = ("SELECT tileset, grid, x, y, z, dim, data FROM tiles%s;" 
                   % (" WHERE " + " AND ".join(where_clauses) 
                      if len(where_clauses) else ""))
            
            cur.execute(sql)
            
            while True:
                row = cur.fetchone()
                if not row:
                    break
                
                yield row[:-1] + (BytesIO(row[-1]),)
    
    def add_tile(self, tileset, grid, dim, x, y, z, f):
        """ Add a new tile entry into the sqlite database file with the given
        values.
        """
        with sqlite3.connect(self.path) as connection:
            cur = connection.cursor()
            cur.execute("INSERT INTO tiles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (tileset, grid, x, y, z, buffer(f.read()), dim, 
                         datetime.now()))
        
        
