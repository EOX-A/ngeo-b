

class IngestionException(Exception):
    """ Base class for ingestion related exceptions. """
    def __init__(self, message=None, code=None):
        super(IngestionException, self).__init__(message)
        self.code = code

class ParsingException(IngestionException):
    pass
