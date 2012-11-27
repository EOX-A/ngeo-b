""" Exception classes. """

class MapCacheException(Exception):
    """ Base class for MapCache related errors. """
    
class SeedException(MapCacheException):
    """ Error when something went wrong in the mapcache_seed utility. """
