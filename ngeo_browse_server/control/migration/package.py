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

import os
from os.path import exists, join, basename
from time import time
import tarfile
from datetime import datetime
import logging
from collections import deque
from cStringIO import StringIO
from io import BytesIO

from django.contrib.gis.geos.geometry import GEOSGeometry
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.resources.coverages.metadata import (
    NativeMetadataFormatEncoder, NativeMetadataFormat
)

from ngeo_browse_server.exceptions import NGEOException


logger = logging.getLogger(__name__)

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
|   |-- <coverage-id1>.tif
|   |-- <coverage-id1>.wkb
|   |-- <coverage-id2>.tif
|   |-- <coverage-id2>.wkb
|   |-- <coverage-id3>.tif
|   |-- <coverage-id3>.wkb
|   `-- ...
`-- (cache)
    `-- <tileset>
        `-- <grid>
            |-- <dim>-<x>-<y>-<z>.png
            |-- <dim>-<x>-<y>-<z>.png
            |-- <dim>-<x>-<y>-<z>.png
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
        self._cache_files = set()
    
    
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
    
    
    def add_browse_metadata(self, name, coverage_id, begin_time, end_time, footprint):
        " Add browse metadata to the archive. "
        
        self._check_dir(SEC_OPTIMIZED)
        encoder = NativeMetadataFormatEncoder()
        xml = DOMElementToXML(encoder.encodeMetadata(coverage_id,
                                                     begin_time, end_time,
                                                     footprint))
        self._add_file(StringIO(xml), join(SEC_OPTIMIZED, name))
        
    
    def add_footprint(self, name, wkb):
        " Add browse metadata to the archive. "
        
        self._check_dir(SEC_OPTIMIZED)
        
        if not name.endswith(".wkb"): name += ".wkb"

        self._add_file(BytesIO(wkb), join(SEC_OPTIMIZED, name))
        

    def add_cache_file(self, tileset, grid, x, y, z, dim, tile_file):
        " Add a cache file to the archive. "

        if (tileset, grid, x, y, z, dim) in self._cache_files:
            return # already inserted

        self._cache_files.add((tileset, grid, x, y, z, dim))
        
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
    
    def _create_info(self, name):
        """ Create a TarInfo object with arbitraty properties set.
        """
        info = tarfile.TarInfo(name)
        info.mtime = time()
        info.uid = os.geteuid()
        info.gid = os.getegid()
        info.mode = 0664
        return info


    def _check_dir(self, name):
        """ Recursively add directory entries to the archive if they do not yet 
            exist. 
        """
        #check all subpaths as well
        dirs = name.split("/")
        for i in range(len(dirs)):
            d = "/".join(dirs[:i+1])
            if not d in self._dirs:
                self._dirs.add(d)
                info = self._create_info(d)
                info.type = tarfile.DIRTYPE
                info.mode = 0775
                self._tarfile.addfile(info)
    
    
    def _add_file(self, f, name):
        """ Add a file-like object `f` to the archive with the given `name`. 
        """
        info = self._create_info(name)

        # set file size
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
    
    
    def get_browse_file(self, filename):
        return self._open_file(join(SEC_OPTIMIZED, filename))
    
    
    def extract_browse_file(self, browse_filename, path=None):
        with open(path, "w+") as f:
            tf = self._tarfile.extractfile(join(SEC_OPTIMIZED, browse_filename))
            f.write(tf.read())
        
    
    def get_browse_file_names(self):
        return self._filter_files(SEC_OPTIMIZED)
    
    
    def get_browse_metadata(self, metadata_filename):
        xml = self._open_file(join(SEC_OPTIMIZED, metadata_filename)).read()
        md_format = NativeMetadataFormat()
        md = md_format.getEOMetadata(xml)
        return md.eo_id, md.begin_time, md.end_time, md.footprint
    
    
    def get_footprint(self, footprint_filename):
        wkb = self._open_file(join(SEC_OPTIMIZED, footprint_filename)).read()
        return GEOSGeometry(buffer(wkb), 4326)

    
    def get_cache_files(self, tileset, grid, dim):
        for member in self._filter_files(join(SEC_CACHE, tileset, grid)):
            name = basename(member.name)
            actual_dim = name[:41] # TODO: replace this
            z, x, y = name[42:].split("-")
            actual_dim = actual_dim.replace("_", "/")
            
            if dim != actual_dim:
                continue
            
            z = int(z)
            x = int(x)
            y = int(y)
            
            yield x, y, z, self._open_file(member)
    
    
    def has_cache(self):
        return self._has_file(SEC_CACHE)
            
    
    def _filter_files(self, d):
        for member in self._tarfile.getmembers():
            if not member.isfile() or not member.name.startswith(d): # TODO: make better path check
                continue
            
            yield member
    
    
    def _open_file(self, name):
        try:
            return self._tarfile.extractfile(name)
        except KeyError:
            raise PackageException("File '%s' is not present in the package."
                                   % name)
        
    def _has_file(self, name):
        try:
            self._tarfile.getmember(name)
            return True
        except KeyError:
            return False

        
    def close(self):
        self._tarfile.close()

    def __enter__(self):
        return self
    
    
    def __exit__(self, etype, value, traceback):
        " End of critical block. Either close/save tarfile or remove it. "

        self.close()


def create(path, compression, force=False):
    if force and exists(path):
        raise PackageException("Output file already exists.")
    elif exists(path):
        os.remove(path)
    
    return PackageWriter(path, compression)


def read(path):
    return PackageReader(path)


def generate_filename(compression):
    now = datetime.utcnow()
    return now.strftime("export_%Y%m%d%H%M%S%f") + COMPRESSION_TO_EXT[compression]


class ImportTransaction(object):
    """ Helper class to keep track of files that need to be removed upon error.
    """
    
    def __init__(self, package_reader, optimized_dir):
        self._package_reader = package_reader
        self._optimized_dir = optimized_dir
        self._filenames = deque()
    
    
    def add_file(self, filename):
        " Add a file to the transaction. "
        self._filenames.append(filename)
    
    
    def __enter__(self):
        " Enter the context. This removes all surveilled files. "
        
        self._filenames.clear()
        return self
        
    
    def __exit__(self, etype, value, traceback):
        """ Exit the context. If an error occurred, all surveilled files are 
            deleted.
        """
        
        if (etype, value, traceback) == (None, None, None):
            self._filenames.clear()
        
        else: # on error
            # remove all files that were added to the transaction
            while self._filenames:
                filename = self._filenames.pop()
                os.remove(filename)

