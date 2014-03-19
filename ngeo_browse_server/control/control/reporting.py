

import re
line = '172.16.0.3 - - [25/Sep/2002:14:04:19 +0200] "GET / HTTP/1.1" 401 - "" "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.1) Gecko/20020827"'
regex = re.compile('([(\d\.)]+) - - \[(.*?)\] "(.*?)" (\d+) - "(.*?)" "(.*?)"')

from collections import namedtuple
from ngeo_browse_server.config import models


print re.match(regex, line).groups()



class Report(object):

    def __init__(self, begin=None, end=None):
        self.begin = end
        self.end = end

    def serialize(self, file):
        report = E("fetchReportDataResponse")
        for record in self.get_records():
            report.append(
                E("report",
                    E("header",
                        E("operation", self.operation),
                        E("component", "test-comp"),
                        E("date", record.date.isoformat("T")), *[
                            E("additionalKey", value, key=key)
                            for key, value in self.get_additional_keys(record)
                        ]
                    ),
                    E("data", *[
                        E("value", value, key=key)
                        for key, value in self.get_data(record)
                    ])
                )
            )


class BrowseAccessReport(Report):
    operation = "BROWSE_ACCESS"

    def get_items(self):
        # TODO: read apache logfile
        pass

    def get_additional_keys(self, record):
        return (
            ("service", record.service),
        )

    def get_data(self, record):
        for key, value in zip(record._fields[2:], record[2]):
            yield key, value


class BrowseReportReport(Report):
    operation = "BROWSE_REPORT"
    def get_records(self):
        browse_reports = models.BrowseReport.objects.all()
        if self.begin is not None:
            browse_reports = browse_reports.filter(
                date_time__gte=self.begin
            )
        if self.end is not None:
            browse_reports = browse_reports.filter(
                date_time__lte=self.end
            )

        for browse_report in browse_reports:
            yield BrowseReportRecord(
                browse_report.date_time, browse_report.browse_layer.browse_type,
                "0", browse_report.responsible_org_name, 
                browse_report.browse_layer.id
            )

    def get_additional_keys(self, record):
        return ()

    def get_data(self, record):
        return record._asdict().items()




BrowseAccessRecord = namedtuple("date", "service", "browselayers", "userid", "authorizationTime", "nTiles", "size", "processingTime", "bbox", "requestTime")
BrowseReportRecord = namedtuple("date", "browseType", "size", "responsibleOrgName", "browseLayers")


