import logging
import subprocess


logger = logging.getLogger(__name__)

def seed_mapcache(seed_command, config_file, tileset, grid, 
                  minx, miny, maxx, maxy, minzoom, maxzoom, threads):

    # translate tileset
    if grid == "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible":
        grid = "G"
    elif grid == "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad":
        grid = "WGS84"
    else:
        raise Exception("Invalid grid '%s'." % grid)
    
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
        "-n", threads
    ]
    
    if minzoom is not None and maxzoom is not None: 
        args.extend(("-z", "%d,%d" % (minzoom, maxzoom)))
    
    
    args = map(str, args)
    
    logger.debug("mapcache seeding command: '%s'. raw: '%s'."
                 % (" ".join(args), args))
    
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    out, err = process.communicate()
    for string in (out, err):
        for line in string.split("\n"):
            logger.info(line)
            
    logger.info("Seeding finished with returncode '%d'." % process.returncode)
    
    return process.returncode