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

from django.shortcuts import render_to_response
from osgeo import gdalnumeric   # This prevents issues in parallel setups. Do 
                                # not remove this line.

from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.config.browsereport.parsing import parse_browse_report
from ngeo_browse_server.control.ingest.exceptions import IngestionException


logger = logging.getLogger(__name__)

def ingest(request):
    """ View to ingest a browse report delivered via HTTP-POST. The XML file is
        expected to be included within the POST data.
    """
    
    try:
        if request.method != "POST":
            e = IngestionException("Method '%s' is not allowed, use 'POST' "
                                   "only." % request.method.upper(),
                                   "MethodNotAllowed")
        
        try:
            document = etree.parse(request)
        except etree.XMLSyntaxError, e: 
            raise IngestionException("Could not parse request XML. Error was: "
                                     "'%s'." % str(e),
                                     "InvalidRequest")
        
        parsed_browse_report = parse_browse_report(document.getroot())
        results = ingest_browse_report(parsed_browse_report)
        
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
