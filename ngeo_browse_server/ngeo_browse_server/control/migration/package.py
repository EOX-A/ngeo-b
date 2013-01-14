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

import os
from os.path import exists, basename, dirname, join
import tarfile
from datetime import datetime

from ngeo_browse_server.control.exceptions import NGEOException

"""
tar-file structure is like that:

archive.tar.gz
|-- browseLayer.xml
|-- reports
|   |-- <browseReport1>.xml
|   |-- <browseReport2>.xml
|   |-- <browseReport3>.xml
|   `-- ...
|-- optimized
|   |-- browse1_proc.tif
|   |-- browse1_proc.xml
|   |-- browse2_proc.tif
|   |-- browse2_proc.xml
|   |-- browse3_proc.tif
|   |-- browse3_proc.xml
|   `-- ...
`-- (cache)
    `-- <tileset>
        `-- <grid>
            |-- <x>-<y>-<z>-<dim>.png
            |-- <x>-<y>-<z>-<dim>.png
            |-- <x>-<y>-<z>-<dim>.png
            `-- ...
"""


COMPRESSION_TO_EXT = {
    "none": ".tar",
    "gzip": ".tar.gz",
    "gz": ".tar.gz",
    "bzip2": ".tar.bz2",
    "bz2": ".tar.bz2"
}

COMPRESSION_TO_SPECIFIER = {
    "none": "",
    "gzip": "gz",
    "gz": "gz",
    "bzip2": "bz2",
    "bz2": "bz2"
}

SEC_REPORTS = "reports"
SEC_OPTIMIZED = "optimized"
SEC_CACHE = "cache"
BROWSE_LAYER_NAME = "browseLayer.xml"

CACHE_FILE_FRMT = "%s-%d-%d-%d"
CACHE_FILE_REGEX = ""

class PackageException(NGEOException):
    pass


class PackageWriter(object):
    "ngEO data migration package writer."
    
    def __init__(self, path, compression):
        " Initialize a package writer. "
        self._path = path
        self._tarfile = tarfile.open(
            path, "w:" + COMPRESSION_TO_SPECIFIER[compression]
        )
        self._dirs = set()
    
    
    def set_browse_layer(self, browse_layer_file):
        " Set the browse layer in the archive. "
        
        self._add_file(browse_layer_file, BROWSE_LAYER_NAME)
    
    
    def add_browse_report(self, browse_report_file, name=None):
        " Add a browse report to the archive. "
        
        if not name:
            name = "TODO"
        self._check_dir(SEC_REPORTS)
        name = join(SEC_REPORTS, name)
        self._add_file(browse_report_file, name)
    
    
    def add_browse(self, browse_file, name):
        " Add a browse file to the achive. "
        
        self._check_dir(SEC_OPTIMIZED)
        name = join(SEC_OPTIMIZED, name)
        self._add_file(browse_file, name)
        

    def add_cache_file(self, tileset, grid, x, y, z, dim, tile_file):
        " Add a cache file to the archive. "
        
        # construct dir name
        d = join(SEC_CACHE, tileset, grid)
        self._check_dir(d)
        
        # replace slashes.
        dim = dim.replace("/", "_")
        
        # construct file name
        name = join(d, CACHE_FILE_FRMT % (dim, z, x, y))
        self._add_file(tile_file, name)
    

    def close(self):
        self._tarfile.close()
    

    def _check_dir(self, name):
        """ Recursively add directory entries to the archive if they do not yet 
        exist. """
        
        #check all subpaths as well
        dirs = name.split("/")
        for i in range(len(dirs)):
            d = "/".join(dirs[:i+1])
            if not d in self._dirs:
                self._dirs.add(d)
                info = tarfile.TarInfo(d)
                info.type = tarfile.DIRTYPE
                self._tarfile.addfile(info)
    
    
    def _add_file(self, f, name):
        " Add a file-like object `f` to the archive with the given `name`. "
        
        info = tarfile.TarInfo(name)
        # get file size
        f.seek(0, os.SEEK_END)
        info.size = f.tell()
        f.seek(0)
        
        # actually insert the file
        self._tarfile.addfile(info, f) 
    
    
    # Section protocol
    
    def __enter__(self):
        return self
    
    
    def __exit__(self, etype, value, traceback):
        " End of critical block. Either close/save tarfile or remove it. "

        # on success
        if (etype, value, traceback) == (None, None, None):
            self.close()
    
        # on error    
        else:
            # remove the archive file
            self.close()
            os.remove(self._path)
    


class PackageReader(object):
    def __init__(self, path):
        self._tarfile = tarfile.open(path, "r:*")
    
    
    
    def get_browse_layer(self):
        return self._open_file(BROWSE_LAYER_NAME)
    
    
    def get_browse_reports(self):
        for member in self._filter_files(SEC_REPORTS):
            yield self._open_file(member)
    
    
    def get_browse_files(self, filename):
        return self._open_file(join(SEC_OPTIMIZED, filename))
    
    
    def get_cache_files(self, tileset, grid):
        for member in self._filter_files(join(SEC_CACHE, tileset, grid)):
            # TODO: x, y, z, dim
            yield self._open_file(member)
    
    
    def has_cache(self):
        return self._has_file(SEC_CACHE)
    
    
    def _filter_files(self, d):
        for member in self._tarfile.getmembers():
            if not member.isfile() or not member.info.startswith(d): # TODO: make better path check
                continue
            
            yield member
    
    
    def _open_file(self, name):
        try:
            self._tarfile.extractfile(name)
        except KeyError:
            raise PackageException("File '%s' is not present in the package."
                                   % name)
        
    def _has_file(self, name):
        try:
            self._tarfile.getmember(name)
            return True
        except KeyError:
            return False
        



def create(path, compression, force=False):
    if force and exists(path):
        raise PackageException("Output file already exists.")
    elif exists(path):
        os.remove(path)
    
    return PackageWriter(path, compression)


def open(path):
    pass


def generate_filename(compression):
    now = datetime.utcnow()
    return now.strftime("export_%Y%m%d%H%M%S%f") + COMPRESSION_TO_EXT[compression]



# TODO
class ArchivedTileSet(object):
    def __init__(self, archive, basepath=None):
        self.archive = archive
        self.basepath = basepath or "cache/"

    
    def __iter__(self):
        # TODO: yield archive/cache entries
        for info in self.archive.getmembers():
            if not info.name.startswith(self.basepath):
                continue
            
            _, tileset, grid = dirname(info.name).split("/")
            x, y, z, dim = basename(info.name).split("-")
            x = float(x); y = float(y); z = int(z)
            
            yield tileset, grid, x, y, z, dim, self.archive.extractfile(info)
            
            # TODO: split filename to "tileset", "grid", "x", "y", "z", "dim", "data"
    
    
        
