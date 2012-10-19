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

from lxml import etree

from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import render_to_response

from ngeo_browse_server.control.ingest import ingest_browse_report



@transaction.commit_on_success
def ingest(request):
    """ View to ingest a browse report delivered via HTTP-POST. The XML file is
        expected to be included within the POST data.
    """
    
    try:
        if request.method != "POST":
            raise Exception("Method '%s' is not allowed, use 'POST' only." % 
                            request.method.upper())
        
        document = etree.parse(request) 
        result = ingest_browse_report(document)
        return render_to_response("control/ingest_response.xml", 
                              {"result": result}, 
                              mime_type="text/xml")
    except Exception, e:
        return render_to_response("control/ingest_exception.xml",
                                  {"code": type(e).__name__,
                                   "message": str(e)},
                                  mime_type="text/xml")
    
    
    
