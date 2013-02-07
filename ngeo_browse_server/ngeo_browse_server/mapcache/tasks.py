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
        raise Exception("Invalid grid '%s'." % grid)
    
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
    ]
    if not delete:
        args.append("-f")
        args.append("-M")
        args.append("8,8")
    
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
