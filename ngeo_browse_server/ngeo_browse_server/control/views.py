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
import traceback
from lxml import etree

from django.conf import settings
from django.shortcuts import render_to_response
from django.utils import simplejson as json
from django.utils import timezone
from osgeo import gdalnumeric   # This prevents issues in parallel setups. Do 
                                # not remove this line.
from eoxserver.processing.preprocessing.exceptions import PreprocessingException 

from ngeo_browse_server import get_version
from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.decoding import XMLDecodeError
from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.config.browsereport.decoding import (
    decode_browse_report, DecodingException
)
from ngeo_browse_server.control.ingest.exceptions import IngestionException
from ngeo_browse_server.control.response import JsonResponse
from ngeo_browse_server.control.control.register import  register, unregister
from ngeo_browse_server.control.control.config import get_instance_id
from ngeo_browse_server.control.control.status import get_status, COMMAND_TO_METHOD


logger = logging.getLogger(__name__)

def ingest(request):
    """ View to ingest a browse report delivered via HTTP-POST. The XML file is
        expected to be included within the POST data.
    """
    
    try:
        if request.method != "POST":
            raise IngestionException("Method '%s' is not allowed, use 'POST' "
                                     "only." % request.method.upper(),
                                     "MethodNotAllowed")
        
        try:
            document = etree.parse(request)
        except etree.XMLSyntaxError, e: 
            raise IngestionException("Could not parse request XML. Error was: "
                                     "'%s'." % str(e),
                                     "InvalidRequest")
        try:
            parsed_browse_report = decode_browse_report(document.getroot())
            results = ingest_browse_report(parsed_browse_report)

        # unify exception code for some exception types
        except (XMLDecodeError, DecodingException), e:
            raise IngestionException(str(e), "InvalidRequest")

        except PreprocessingException, e:
            raise IngestionException(str(e))            

        
        return render_to_response("control/ingest_response.xml", 
                              {"results": results}, 
                              mimetype="text/xml")
    except Exception, e:
        logger.debug(traceback.format_exc())
        return render_to_response("control/ingest_exception.xml",
                                  {"code": getattr(e, "code", None)
                                           or type(e).__name__,
                                   "message": str(e)},
                                  mimetype="text/xml")


def controller_server(request):
    config = get_ngeo_config()
    try:
        values = json.load(request)

        # POST means "register"
        if request.method == "POST":
            register(
                values["instanceId"], values["instanceType"],
                values["controllerServerId"], get_client_ip(request), config
            )

        # DELETE means "unregister"
        elif request.method == "DELETE":
            unregister(
                values["instanceId"], values["controllerServerId"],
                get_client_ip(request), config
            )

    except Exception as e:
        logger.error(traceback.format_exc())
        instance_id = get_instance_id(config)
        values = {
            "faultString": str(e),
            "instanceId": instance_id, 
            "reason": getattr(e, "reason", "NO_CODE")
        }
        if settings.DEBUG:
            values["traceback"] = traceback.format_exc()
        return JsonResponse(values, status=400)

    return JsonResponse({"result": "SUCCESS"})


def status(request):
    if request.method == "GET":
        return JsonResponse({
            "timestamp": timezone.now().isoformat(),
            "state": get_state(),
            "softwareversion": get_version(),
            "queues": [
                # TODO: find relevant status queues
                #{"name": "request1",
                #"counters": [{
                #    "name": "counter1",
                #    "value": 2
                #}, {
                #    "name": "counter2",
                #    "value": 2
                #}]}
            ]
        })

    elif request.method == "PUT":
        # set status
        pass


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    else:
        return request.META.get('REMOTE_ADDR')

