#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

import re
from os.path import join
import logging
import urllib2
import time
from datetime import datetime

from collections import namedtuple
from lxml import etree
from lxml.builder import E
from django.conf import settings
from eoxserver.core.util.timetools import isotime, getDateTime

from ngeo_browse_server.config import models
from ngeo_browse_server.config import get_ngeo_config, safe_get
from ngeo_browse_server.control.control.config import (
    get_controller_config, get_controller_config_path, get_instance_id,
    CONTROLLER_SERVER_SECTION
)


logger = logging.getLogger(__name__)


#line = '172.16.0.3 - - [25/Sep/2002:14:04:19 +0200] "GET / HTTP/1.1" 401 - "" "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.1) Gecko/20020827"'
class Report(object):
    operation = None
    def __init__(self, begin=None, end=None):
        self.begin = end
        self.end = end


class BrowseAccessReport(Report):
    operation = "BROWSE_ACCESS"

    def get_records(self):
        regex = re.compile('(.*?) ([(\d\.)]+) - - \[(.*?)\] "(.*?)" (\d+) (\d+|-)')
        with open("/var/log/mapcache_log") as f:
            for line in f:

                # TODO: implement
                print line
                _, ip, raw_datetime, request, raw_status, raw_size = regex.match(line).groups()

                if int(raw_status) not in (200, 304):
                    continue

                try: 
                    size = int(raw_size)
                except ValueError:
                    size = 0

                #("date", "service", "browselayers", "userid", "authorizationTime", "nTiles", "size", "processingTime", "bbox", "requestTime")

                yield BrowseAccessRecord(
                    datetime(*time.strptime(raw_datetime, "%d/%b/%Y:%H:%M:%S +0000")[0:6]),
                    "WMTS", "layers", ip, "0", "0", str(size), "0", "0,0,0,0", "start/stop"
                )

    def get_additional_keys(self, record):
        return (
            ("service", record.service),
        )

    def get_data(self, record):
        for key, value in zip(record._fields[2:], record[2:]):
            yield key, value


class BrowseReportReport(Report):
    operation = "BROWSE_REPORT"
    def get_records(self):
        
        try:
            filename = settings.LOGGING["handlers"]["ngEO-ingest"]["filename"]
        except KeyError:
            # TODO: cannot produce record
            logger.error(
                "Ingest log not configured! Cannot produce ingest reports."
            )
            return

        with open(filename) as f:
            for line in f:
                items = line[:-1].split("/\\/\\")
                date = getDateTime(items[0])
                if self.end and self.end < date:
                    continue
                elif self.begin and self.begin > date:
                    continue
                yield BrowseReportRecord(date, *items[1:])

    def get_additional_keys(self, record):
        return ()

    def get_data(self, record):
        return [(key, value) for key, value in record._asdict().items() if key != "date"]

BrowseAccessRecord = namedtuple("BrowseAccessRecord", ("date", "service", "browselayers", "userid", "authorizationTime", "nTiles", "size", "processingTime", "bbox", "requestTime"))
BrowseReportRecord = namedtuple("BrowseReportRecord", ("date", "responsibleOrgName", "dateTime", "browseType", "numberOfContainedBrowses", "numberOfSuccessfulBrowses", "numberOfFailedBrowses"))

def get_report_xml(begin, end, types):
    # TODO: read from config
    component_name = "test"

    root = E("fetchReportDataResponse")
    for report_type in types:
        report = report_type(begin, end)
        for record in report.get_records():
            root.append(
                E("report",
                    E("header",
                        E("operation", report.operation),
                        E("component", component_name),
                        E("date", isotime(record.date)), *[
                            E("additionalKey", value, key=key)
                            for key, value in report.get_additional_keys(record)
                        ]
                    ),
                    E("data", *[
                        E("value", value, key=key)
                        for key, value in report.get_data(record)
                    ])
                )
            )
    return root


def send_report(ip_address=None, begin=None, end=None, types=(BrowseReportReport, BrowseAccessReport), config=None):
    config = config or get_ngeo_config()

    try:
        if not ip_address:
            ctrl_config = get_controller_config(get_controller_config_path(config))
            ip_address = safe_get(ctrl_config, CONTROLLER_SERVER_SECTION, "address")
    except IOError:
        # probably no config file present, so IP cannot be determined.
        pass

    if not ip_address:
        raise Exception("IP address could not be determined")

    tree = get_report_xml(begin, end, types)
    req = urllib2.Request(
        url="http://%s/notify" % ip_address,
        data=etree.tostring(tree, pretty_print=True),
        headers={'Content-Type': 'text/xml'}
    )
    print req.data
    try:
        urllib2.urlopen(req, timeout=10)
    except (urllib2.HTTPError, urllib2.URLError), e:
        logger.error(
            "Could not send report (%s): '%s'" % (type(e).__name__, str(e))
        )
        raise


def save_report(filename, begin=None, end=None, types=(BrowseReportReport, ), config=None):
    config = config or get_ngeo_config()
    tree = get_report_xml(begin, end, types)
    
    with open(filename, "w+") as f:
        f.write(etree.tostring(tree, pretty_print=True))
