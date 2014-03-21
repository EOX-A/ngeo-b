#! /usr/bin/python
#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

import sys
from optparse import OptionParser
from lxml import etree


def request_authorization(baseurl, user, layer, timeperiod):
    """ Function, that sends an HTTP GET request to the given ngEO Web Server.
    """
    try:
        url = (
            "%s/BrwsAuthorizationCheck?UserId=%s&BrowseLayerId=%s&TimePeriod=%s" 
            % (baseurl if not baseurl.endswith("/") else baseurl[:-1], 
               user, layer, timeperiod
            )
        )

        root = etree.parse(url).getroot()
        code = root.findtext(
            "{http://ngeo.eo.esa.int/schema/webserver}ResponseCode"
        )

        if code == "AUTHORIZED":
            return True

    except (etree.XMLSyntaxError, IOError, IndexError), e:
        # IOError: when HTTP request failed
        # IndexError: when parsing the XML and no ResponseCode element is present
        pass

    return False


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-b", "--baseurl", dest="baseurl",
                      help="URL of ngEO WebServer")
    parser.add_option("-u", "--user", dest="user",
                      help="The authenticated user name.")
    parser.add_option("-l", "--layer", dest="layer",
                      help="The layer.")
    parser.add_option("-t", "--timeperiod", dest="timeperiod",
                      help="The time period.")

    opts, _ = parser.parse_args()

    authorized = request_authorization(
        opts.baseurl, opts.user, opts.layer, opts.timeperiod
    )

    sys.exit(0 if authorized else 1)
