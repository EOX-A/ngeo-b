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
    get_ngeo_config, get_project_relative_path, safe_get
)
from ngeo_browse_server.lock import (FileLock, LockException)
from ngeo_browse_server.mapcache.exceptions import (
    SeedException, LayerException
)
from ngeo_browse_server.mapcache.tileset import URN_TO_GRID
from ngeo_browse_server.mapcache.config import (
    get_mapcache_seed_config, get_tileset_path
)


# Maximum bounds for both supported CRSs
CRS_BOUNDS = {
    3857: (-20037508.3428, -20037508.3428, 20037508.3428, 20037508.3428),
    4326: (-180, -90, 180, 90)
}

GRID_TO_SRID = {
    "GoogleMapsCompatible": 3857,
    "WGS84": 4326
}


logger = logging.getLogger(__name__)

def seed_mapcache(seed_command, config_file, tileset, grid,
                  minx, miny, maxx, maxy, minzoom, maxzoom,
                  start_time, end_time, threads, delete):

    # translate grid URN to mapcache grid name
    try:
        grid = URN_TO_GRID[grid]
    except KeyError:
        raise SeedException("Invalid grid '%s'." % grid)

    bounds = CRS_BOUNDS[GRID_TO_SRID[grid]]
    full = float(abs(bounds[0]) + abs(bounds[2]))

    dateline_crossed = False
    if maxx>bounds[2]:
        dateline_crossed = True
    # extent is always within [bounds[0],bounds[2]]
    # where maxx can be >bounds[2] but <=full
    if minx<bounds[0] or minx>bounds[2] or maxx<bounds[0] or maxx>full:
        raise SeedException("Invalid extent '%s,%s,%s,%s'."
                            % (minx, miny, maxx, maxy))

    if minzoom is None: minzoom = 0
    if maxzoom is None: maxzoom = 6

    # start- and end-time are expected to be UTC Zulu
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)

    logger.info("Starting mapcache seed with parameters: command='%s', "
                "config_file='%s', tileset='%s', grid='%s', "
                "extent='%s,%s,%s,%s', zoom='%s,%s', threads='%s', mode='%s'."
                % (seed_command, config_file, tileset, grid,
                  minx, miny, maxx, maxy, minzoom, maxzoom, threads,
                  "seed" if not delete else "delete"))

    seed_args = [
        seed_command,
        "-c", config_file,
        "-t", tileset,
        "-g", grid,
        "-e", "%f,%f,%f,%f" % (minx, miny, bounds[2] if dateline_crossed else maxx, maxy),
        "-n", str(threads),
        "-z", "%d,%d" % (minzoom, maxzoom),
        "-D", "TIME=%sZ/%sZ" % (start_time.isoformat(), end_time.isoformat()),
        "-m", "seed" if not delete else "delete",
        "-q",
        "-M", "8,8",
    ]
    if not delete:
        seed_args.append("-f")


    try:
        config = get_ngeo_config()
        timeout = safe_get(config, "mapcache.seed", "timeout")
        timeout = float(timeout) if timeout is not None else 60.0
    except:
        timeout = 60.0


    try:
        lock = FileLock(
            get_project_relative_path("mapcache_seed.lck"), timeout=timeout
        )

        with lock:
            logger.debug("mapcache seeding command: '%s'. raw: '%s'."
                         % (" ".join(seed_args), seed_args))
            process = subprocess.Popen(seed_args, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

            out, err = process.communicate()
            for string in (out, err):
                for line in string.split("\n"):
                    if line != '':
                        logger.info("MapCache output: %s" % line)

        if process.returncode != 0:
            raise SeedException("'%s' failed. Returncode '%d'."
                                % (seed_command, process.returncode))

        # seed second extent if dateline is crossed
        if dateline_crossed:
            with lock:
                index = seed_args.index("%f,%f,%f,%f" % (minx, miny, bounds[2], maxy))
                seed_args[index] = "%f,%f,%f,%f" % (bounds[0], miny, maxx-full, maxy)
                logger.debug("mapcache seeding command: '%s'. raw: '%s'."
                             % (" ".join(seed_args), seed_args))
                process = subprocess.Popen(seed_args, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)

                out, err = process.communicate()
                for string in (out, err):
                    for line in string.split("\n"):
                        if line != '':
                            logger.info("MapCache output: %s" % line)

            if process.returncode != 0:
                raise SeedException("'%s' failed. Returncode '%d'."
                                    % (seed_command, process.returncode))

    except LockException, e:
        raise SeedException("Seeding failed: %s" % str(e))

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
        raise LayerException(
            "Cannot add browse layer to mapcache config, because a layer with "
            "the name '%s' is already inserted." % name
        )

    tileset_path = get_tileset_path(browse_layer.browse_type)

    bounds = CRS_BOUNDS[GRID_TO_SRID[URN_TO_GRID[browse_layer.grid]]]
    full = float(abs(bounds[0]) + abs(bounds[2]))

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
            E("metadata",
                E("title", str(browse_layer.title)),
                *([
                    E("abstract", str(browse_layer.description))]
                    if browse_layer.description
                    else []
                )
            ),
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
                E("query", "select strftime('%Y-%m-%dT%H:%M:%SZ',start_time)||'/'||strftime('%Y-%m-%dT%H:%M:%SZ',end_time) from time where source_id=:tileset and (start_time<datetime(:end_timestamp,'unixepoch') and (end_time>datetime(:start_timestamp,'unixepoch')) or (start_time=end_time and start_time<=datetime(:end_timestamp,'unixepoch') and end_time>=datetime(:start_timestamp,'unixepoch'))) and ((maxx>=:minx and minx<=:maxx) or (maxx>"+str(bounds[2])+" and (maxx-"+str(full)+")>=:minx and (minx-"+str(full)+")<=:maxx)) and maxy>=:miny and miny<=:maxy order by end_time asc limit "+str(browse_layer.tile_query_limit)),
                type="sqlite", default=str(browse_layer.timedimension_default)),
            *([
                E("auth_method", "cmdlineauth")]
                if browse_layer.browse_access_policy in ("RESTRICTED", "PRIVATE")
                else []
            ),
            name=name
        )
    ])

    logger.info("Adding cache, source, and tileset for '%s'." % name)
    write_mapcache_xml(root, config)


@lock_mapcache_config
def remove_mapcache_layer_xml(browse_layer, config=None):
    config = config or get_ngeo_config()

    name = browse_layer.id

    root = read_mapcache_xml(config)

    logger.info("Removing cache, source, and tileset for '%s'." % name)
    try:
        root.remove(root.xpath("cache[@name='%s']" % name)[0])
        root.remove(root.xpath("source[@name='%s']" % name)[0])
        root.remove(root.xpath("tileset[@name='%s']" % name)[0])
    except IndexError:
        raise LayerException(
            "Failed to remove browse layer from mapcache config, because a "
            "layer with the name '%s' could not be found." % name
        )
    write_mapcache_xml(root, config)
