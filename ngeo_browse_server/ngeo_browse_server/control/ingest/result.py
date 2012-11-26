


class IngestResult(object):
    """ Result object for ingestion operations. """
    
    def __init__(self):
        self._inserted = 0
        self._replaced = 0
        self._records = []
    
    
    def add(self, identifier, replaced=False, status="success"):
        """ Adds a single browse ingestion result, where the status is either
        success or failure.
        """
        if replaced:
            self._replaced += 1
        else:
            self._inserted += 1
        
        assert(status in ("success", "partial"))
        
        self._records.append((identifier, status, None, None))
    
    
    def add_failure(self, identifier, code, message):
        """ Add a single browse ingestion failure result, whith an according 
        error code and message.
        """
        self._records.append((identifier, "failure", code, message))


    def __iter__(self):
        "Helper for easy iteration of browse ingest results."
        return iter(self._records)
    
    
    @property
    def status(self):
        """Returns 'partial' if any failure results where registered, else 
        'success'.
        """
        if len(filter(lambda record: record[1] == "failure", self._records)):
            return "partial"
        else:
            return "success"
    
    to_be_replaced = property(lambda self: len(self._records))  
    actually_inserted = property(lambda self: self._inserted)
    actually_replaced = property(lambda self: self._replaced)

    
