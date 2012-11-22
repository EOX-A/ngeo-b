import logging
import subprocess

logger = logging.getLogger(__name__)

def seed_mapcache(seed_command, config_file, tileset, grid, 
                  minx, miny, maxx, maxy, minzoom, maxzoom, threads):
    
    logger.info("Starting mapcaching seed with parameters: command='%s', "
                "config_file='%s', tileset='%s', grid='%s', "
                "extent='%s,%s,%s,%s', zoom='%s,%s', threads='%s'." 
                % (seed_command, config_file, tileset, grid, 
                  minx, miny, maxx, maxy, minzoom, maxzoom, threads))
    
    cmd = ("%s -c %s -t %s -g %s -e %f,%f,%f,%f -n %d" %
           (seed_command, config_file, tileset, grid, 
            minx, miny, maxx, maxy, threads))
    
    if minzoom is not None and maxzoom is not None: 
        cmd += " -z %d,%d" % (minzoom, maxzoom)
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    out, err = process.communicate()
    for stream in (out, err):
        for line in stream.readlines():
            logger.info(line)
    
    return process.returncode
