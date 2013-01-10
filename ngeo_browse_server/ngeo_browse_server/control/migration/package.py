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


class PackageException(NGEOException):
    pass


class PackageWriter(object):
    def __init__(self, path, compression):
        self._path = path
        self._tarfile = tarfile.open(
            path, "w:" + COMPRESSION_TO_SPECIFIER[compression]
        )
    
    
    def set_browse_layer(self, browse_layer_file):
        info = tarfile.TarInfo("browseLayer.xml")
        self._tarfile.addfile(info, browse_layer_file)
    
    
    def add_browse_report(self, browse_report_file, name=None):
        if not name:
            name = "TODO"
        info = tarfile.TarInfo(join("reports", name))
        self._tarfile.addfile(info, browse_report_file)
    
    
    def add_browse(self, browse_file, name):
        info = tarfile.TarInfo(join("optimized", name))
        self._tarfile.addfile(info, browse_file)
    
    
    def add_cache_file(self, tileset, grid, x, y, z, dim):
        pass
    
    
    def __enter__(self):
        return self
    
    def __exit__(self, etype, value, traceback):
        " End of critical block. Either close/save tarfile or remove it. "

        # on success
        if (etype, value, traceback) == (None, None, None):
            # TODO: error handling
            self.close()
        
        else:
            # remove the archive file
            self.close()
            os.remove(self._path)
    
    
    def close(self):
        self._tarfile.close()


def create(path, compression, force=False):
    if force and exists(path):
        print "P"
        raise PackageException("Output file already exists.")
    elif exists(path):
        os.remove(path)
    
    print "P"
    
    return PackageWriter(path, compression)


def open(path):
    pass


def generate_filename(compression):
    now = datetime.utcnow()
    return now.strftime("export_%Y%m%d%H%M%S%f") + COMPRESSION_TO_EXT[compression]


def save(pacakge, path):
    if exists(path):
        os.remove(path)
    
    archive = tarfile.open(path, "w:gz")
    
    # TODO:
    #  - serialize the browse report to XML and save it as BrowseReport.xml in 
    #    the root of the tarfile
    #  - add a folder `browses` to the archive root
    #  - loop over all browses in the report and get the filename. Add the file
    #    to the archive.
    #  - if a cache is present, create a folder structure cache/<tileset>/<grid>/
    #  - loop over all items in the cache tileset, create a filename like ...
    #    and save the cache tile under that name in the folder in the archive

def load(path):
    pass


class Package(object):
    def __init__(self, browse_report, cache_tileset=None):
        self.browse_report = browse_report
        self.cache_tileset = cache_tileset

    def save(self, path):
        save(self, path)


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
    
    
        
