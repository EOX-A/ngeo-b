
import sys
import urllib2
from optparse import OptionParser

from lxml import etree


def request_authorization(baseurl, user, layer, timeperiod):
    """ Function, that sends an HTTP GET request to the given ngEO Web Server.
    """
    try:
        url = (
            "%s/BrwsAuthorizationCheck?UserId=%s&BrowseLayerId=%s&TimePeriod=%s" 
            % (baseurl, user, layer, timeperiod) 
        )

        with urllib2.urlopen(url) as f:
            root = lxml.parse(f)

        namespaces = {"ws", "http://ngeo.eo.esa.int/schema/webserver"}
        code = root.xpath("ws:ResponseCode/text()", namespaces=namespaces)[0]

        if code == "AUTHORIZED":
            return True

    except (urllib2.URLError, etree.XMLSyntaxError, IndexError):
        # IndexError: when parsing the XML and no responseCode is present
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

    options, _ = parser.parse_args()

    sys.exit(0 if request_authorization(**options) else 1)
