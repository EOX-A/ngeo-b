from django.http import HttpResponse
from django.util import simplejson as json


class JsonResponse(HttpResponse):
    "Reponse class for JSON data."
    
    def __init__(self, content, mimetype=None, status=None, content_type=None):
        if mimetype is None:
            mimetype = 'application/json'

        if not isinstance(content, basestring):
            content=json.dumps(content)

        super(JsonResponse, self).__init__(
            content=content,
            mimetype=mimetype,
            status=status,
            content_type=content_type,
        )
