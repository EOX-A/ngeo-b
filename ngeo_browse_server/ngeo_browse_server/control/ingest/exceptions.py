

class IngestionException(Exception):
    """ Base class for ingestion related exceptions. """
    pass

class ParsingException(IngestionException):
    pass