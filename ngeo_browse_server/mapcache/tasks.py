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
import subprocess
from functools import wraps

from lxml import etree
from lxml.builder import E
from django.conf import settings
from django.core.urlresolvers import reverse

from ngeo_browse_server.config import (
    get_ngeo_config, get_project_relative_path
)
from ngeo_browse_server.lock import FileLock
from ngeo_browse_server.mapcache.exceptions import SeedException
from ngeo_browse_server.mapcache.tileset import URN_TO_GRID
from ngeo_browse_server.mapcache.config import (
    get_mapcache_seed_config, get_tileset_path
)


logger = logging.getLogger(__name__)

def seed_mapcache(seed_command, config_file, tileset, grid, 
                  minx, miny, maxx, maxy, minzoom, maxzoom,
                  start_time, end_time, threads, delete):

    # translate grid URN to mapcache grid name
    try:
        grid = URN_TO_GRID[grid]
    except KeyError:
        raise SeedException("Invalid grid '%s'." % grid)
    
    if minzoom is None: minzoom = 0
    if maxzoom is None: maxzoom = 10
    
    # start- and end-time are expected to be UTC Zulu 
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)
    
    logger.info("Starting mapcaching seed with parameters: command='%s', "
                "config_file='%s', tileset='%s', grid='%s', "
                "extent='%s,%s,%s,%s', zoom='%s,%s', threads='%s'." 
                % (seed_command, config_file, tileset, grid, 
                  minx, miny, maxx, maxy, minzoom, maxzoom, threads))
    
    args = [
        seed_command,
        "-c", config_file,
        "-t", tileset,
        "-g", grid,
        "-e", "%f,%f,%f,%f" % (minx, miny, maxx, maxy),
        "-n", str(threads),
        "-z", "%d,%d" % (minzoom, maxzoom),
        "-D", "TIME=%sZ/%sZ" % (start_time.isoformat(), end_time.isoformat()),
        "-m", "seed" if not delete else "delete",
        "-q",
        "-M", "8,8",
    ]
    if not delete:
        args.append("-f")
    
    logger.debug("mapcache seeding command: '%s'. raw: '%s'."
                 % (" ".join(args), args))
    
    process = subprocess.Popen(args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    
    out, err = process.communicate()
    for string in (out, err):
        for line in string.split("\n"):
            logger.info(line)
    
    if process.returncode != 0:
        raise SeedException("'%s' failed. Returncode '%d'."
                            % (seed_command, process.returncode))
    
    logger.info("Seeding finished with returncode '%d'." % process.returncode)
    
    return process.returncode



def lock_mapcache_config(func):
    """ Decorator for functions involving the mapcache configuration to lock 
        the mapcache configuration.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        config = get_ngeo_config()
        mapcache_config = get_mapcache_seed_config(config)
        with FileLock(get_project_relative_path("mapcache.xml.lck")):
            return func(*args, **kwargs)
    return wrapper


def read_mapcache_xml(config):
    mapcache_config = get_mapcache_seed_config(config)
    mapcache_xml_filename = mapcache_config["config_file"]
    with open(mapcache_xml_filename) as f:
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.parse(f, parser).getroot()


def write_mapcache_xml(root, config):
    mapcache_config = get_mapcache_seed_config(config)
    mapcache_xml_filename = mapcache_config["config_file"]
    with open(mapcache_xml_filename, "w") as f:
        f.write(etree.tostring(root, pretty_print=True))


@lock_mapcache_config
def add_mapcache_layer_xml(browse_layer, config=None):
    name = browse_layer.id

    config = config or get_ngeo_config()

    root = read_mapcache_xml(config)

    if len(root.xpath("cache[@name='%s']|source[@name='%s']|tileset[@name='%s']" % (name, name, name))):
        raise Exception(
            "Cannot add browse layer to mapcache config, because a layer with "
            "the name '%s' is already inserted." % name
        )

    tileset_path = get_tileset_path(browse_layer.browse_type)

    root.extend([
        E("cache", 
            E("dbfile", tileset_path),
            E("detect_blank", "true"),
            name=name, type="sqlite3"
        ),
        E("source",
            E("getmap", 
                E("params",
                    E("LAYERS", name),
                    E("TRANSPARENT", "true")
                )
            ),
            E("http", 
                E("url", "http://localhost/browse/ows?")
            ),
            name=name, type="wms"
        ),
        E("tileset",
            E("source", name),
            E("cache", name),
            E("grid", 
                URN_TO_GRID[browse_layer.grid], **{
                    "max-cached-zoom": str(browse_layer.highest_map_level),
                    "out-of-zoom-strategy": "reassemble"
                }
            ),
            E("format", "mixed"),
            E("metatile", "8 8"),
            E("expires", "3600"),
            E("read-only", "true"),
            E("timedimension",
                E("dbfile", settings.DATABASES["mapcache"]["NAME"]),
                E("query", "select strftime('%Y-%m-%dT%H:%M:%SZ',start_time)||'/'||strftime('%Y-%m-%dT%H:%M:%SZ',end_time) from time where source_id=:tileset and start_time<=datetime(:end_timestamp,'unixepoch') and end_time>=datetime(:start_timestamp,'unixepoch') and maxx>=:minx and maxy>=:miny and minx<=:maxx and miny<=:maxy order by end_time desc limit 100"),
                type="sqlite", default="2010" # TODO: default year into layer definition
            ), *([
                E("auth_method", "cmdlineauth")] 
                if browse_layer.browse_access_policy in ("RESTRICTED", "PRIVATE")
                else []
            ),
            name=name
        )
    ])

    write_mapcache_xml(root, config)


@lock_mapcache_config
def remove_mapcache_layer_xml(browse_layer, config=None):
    config = config or get_ngeo_config()

    name = browse_layer.id

    root = read_mapcache_xml(config)

    root.remove(root.xpath("cache[@name='%s']" % name)[0])
    root.remove(root.xpath("source[@name='%s']" % name)[0])
    root.remove(root.xpath("tileset[@name='%s']" % name)[0])

    write_mapcache_xml(root, config)
