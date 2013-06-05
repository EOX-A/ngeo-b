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

from ngeo_browse_server.mapcache.exceptions import SeedException
from ngeo_browse_server.mapcache.tileset import URN_TO_GRID


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
