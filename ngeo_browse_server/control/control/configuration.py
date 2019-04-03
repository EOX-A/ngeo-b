#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 European Space Agency
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

from lxml.builder import ElementMaker, E

from ngeo_browse_server.config import (
    get_ngeo_config, write_ngeo_config, safe_get
)
from ngeo_browse_server.mapcache.tasks import (
    lock_mapcache_config, read_mapcache_xml, write_mapcache_xml
)


ns_xsd_prefix = "xsd"
ns_xsd_uri = "http://www.w3.org/2001/XMLSchema"
ns_xsd = lambda s: ("{%s}%s" % (ns_xsd_uri, s))
XSD = ElementMaker(namespace=ns_xsd_uri, nsmap={ns_xsd_prefix: ns_xsd_uri})

TYPE_MAP = {
    bool: (lambda s: s == "true" or s == "True")
}

ENCODE_MAP = {
    bool: (lambda b: "true" if b else "false")
}

SCHEMA_MAP = {
    bool: "%s:boolean" % ns_xsd_prefix,
    int: "%s:integer" % ns_xsd_prefix,
    str: "%s:string" % ns_xsd_prefix,
}


class Parameter(object):
    def __init__(self, type, name, title, description, default=None,
                 allowed_values=None):
        self.type = type
        self.name = name
        self.title = title
        self.description = description
        self.default = default
        self.allowed_values = allowed_values

    @property
    def type_name(self):
        if not self.allowed_values:
            return SCHEMA_MAP[self.type]
        return self.name + "Type"

    def get_allowed_values_enumeration(self, value, documentation):
        return XSD("enumeration",
            XSD("annotation",
                XSD("documentation",
                    XSD("tooltip", documentation)
                )
            ), value=value
        )

    def get_schema_type(self):
        if not self.allowed_values:
            return None
        else:
            return XSD("simpleType",
                XSD("restriction", *[
                        self.get_allowed_values_enumeration(value, documentation)
                        for value, documentation in self.allowed_values
                    ], base="%s:string" % ns_xsd_prefix
                ), name=self.type_name
            )

    def get_schema_element(self):
        return XSD("element",
            XSD("annotation",
                XSD("documentation",
                    XSD("label", self.title),
                    XSD("tooltip", self.description)
                )
            ),
            name=self.name, type=self.type_name
        )

    def parse(self, element):
        return TYPE_MAP.get(self.type, self.type)(element)

    def encode(self, value):
        return E(self.name, ENCODE_MAP.get(self.type, str)(value))


class ConfiguratorException(Exception):
    pass


class Configurator(object):
    type_name = None
    element_name = None

    def parse(self, element):
        kwargs = {}

        for parameter in self.parameters:
            value_element = element.find(parameter.name)
            if value_element is None:
                raise ConfiguratorException("Element '%s/%s' not found" % (
                    self.element, parameter.name
                ))

            kwargs[value_element.tag] = parameter.parse(value_element.text)

        self.set_values(**kwargs)

    def encode(self):
        values = self.get_values()
        return E(self.element_name, *[
            parameter.encode(values[parameter.name])
            for parameter in self.parameters
        ])

    def get_schema_type(self):
        return XSD("complexType",
            XSD("sequence", *[
                parameter.get_schema_element()
                for parameter in self.parameters
            ]), name=self.type_name
        )

    def get_parameter_schema_types(self):
        return [
            parameter.get_schema_type()
            for parameter in self.parameters
            if parameter.get_schema_type() is not None
        ]

    def get_schema_element(self):
        return XSD("element", name=self.element_name, type=self.type_name)

    # interface methods

    parameters = ()

    def set_values(self, **kwargs):
        raise NotImplementedError()

    def get_values(self):
        raise NotImplementedError()


class ngEOConfigConfigurator(Configurator):
    section = None

    def get_value(self, parameter, config):
        parser = TYPE_MAP.get(parameter.type, parameter.type)

        try:
            return parser(config.get(self.section, parameter.name))
        except:
            if parameter.default is not None:
                return parameter.default
            raise

    def get_values(self):
        config = get_ngeo_config()
        return dict([
            (parameter.name, self.get_value(parameter, config))
            for parameter in self.parameters
        ])

    def set_values(self, **kwargs):
        config = get_ngeo_config()
        section = self.section
        for key, value in kwargs.items():
            config.set(self.section, key, value)


class IngestConfigurator(ngEOConfigConfigurator):

    type_name = "ingestType"
    element_name = "ingest"

    section = "control.ingest"

    parameters = (
        Parameter(
            str, "optimized_files_postfix", "Browse file postfix",
            "String that is attached at the end of filenames of optimized "
            "browses.", "_proc"
        ),
        Parameter(
            str, "compression", "Compression method",
            'Compression method used. One of "JPEG", "LZW", "PACKBITS", '
            '"DEFLATE", "CCITTRLE", "CCITTFAX3", "CCITTFAX4", or "NONE". '
            'Default is "NONE"', "NONE"
        ),
        Parameter(
            int, "jpeg_quality", "JPEG compression quality",
            'JPEG quality if compression is "JPEG". Integer between 1-100. ',
            "75"
        ),
        Parameter(
            str, "zlevel", "DEFLATE Compression level",
            'zlevel option for "DEFLATE" compression. Integer between 1-9.',
            "6"
        ),
        Parameter(
            bool, "tiling", "Internal tiling",
            "Defines whether or not the browse images shall be internally "
            "tiled.", "true"
        ),
        Parameter(
            bool, "overviews", "Generate overviews",
            "Defines whether internal browse overviews shall be generated.",
            "true"
        ),
        Parameter(
            str, "overview_resampling", "Overview resampling",
            'Defines the resampling method used to generate the overviews. '
            'One of "NEAREST", "GAUSS", "CUBIC", "AVERAGE", "MODE", '
            '"AVERAGE_MAGPHASE" or "NONE".', "NEAREST"
        ),
        Parameter(
            str, "overview_levels", "Overview levels",
            'A comma separated list of integer overview levels. Defaults to '
            'a automatic selection of overview levels according to the '
            'dataset size.', "2,4,8,16"
        ),
        Parameter(
            int, "overview_minsize", "Overview minimum size",
            "A (positive) integer value declaring the lowest size the highest "
            "overview level at most shall have.", "256"
        ),
        Parameter(
            bool, "color_index", "Color index table",
            "Defines if a color index shall be calculated.", "false"
        ),
        Parameter(
            bool, "footprint_alpha", "",
            "Defines whether or not a alpha channel shall be used to display "
            "the images area of interest.", "false"
        ),
        Parameter(
            int, "sieve_max_threshold", "",
            "Sets the maximum threshold for the sieve algorithm. See "
            "`http://www.gdal.org/gdal__alg_8h.html#a33309c0a316b223bd33ae5753cc7f616` "
            "for details. Defaults to the number of pixels divided by 16 "
            "which is indicated by a value of 0.", "0"
        ),
        Parameter(
            int, "simplification_factor", "",
            "Sets the factor for the simplification algorithm. See "
            "`http://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm` "
            "for details. Defaults to 2 (2 * resolution == 2 pixels) which "
            "provides reasonable results.", "2"
        ),
        Parameter(
            bool, "regular_grid_clipping", "Regular Grid clipping",
            "Clip the regular grid tie points pixel coordinates to be inside "
            "of the image bounds. Necessary for Sentinel-1 image data.",
            "false"
        ),
        Parameter(
            bool, "in_memory", "Perform pre-processing in memory",
            "Defines if all all pre-processing is done with in-memory "
            "datasets. For smaller ones, this might be beneficial in terms "
            "of performance, but it is safer to directly use files (which "
            "is the default).", "false"
        ),
        Parameter(
            str, "threshold", "Merge time threshold",
            "The maximum time difference between the two browse report to "
            "allow a 'merge'. E.g: 1w 5d 3h 12m 18ms. Defaults to '5h'.", "5h"
        ),
        Parameter(
            str, "strategy", "Indent browse strategy",
            "Sets the 'strategy' for when an ingested browse is equal with an "
            "existing one. The 'merge'-strategy tries to merge the two "
            "existing images to one single. This is only possible if the time "
            "difference of the two browse reports (the report of the to be "
            "ingested browse and the one of the already existing one) is "
            "lower than the threshold. Otherwise a 'replace' is done. "
            "The 'replace' strategy removes the previous browse, before "
            "ingesting the new one. The 'skip' strategy skips the ingestion "
            "when the new browse is not newer than the already ingested one."
            "Defaults to 'replace'.", "merge"
        ),
    )


class CacheConfigurator(ngEOConfigConfigurator):
    section = "mapcache.seed"

    type_name = "cacheType"
    element_name = "cache"

    parameters = (
        Parameter(
            int, "threads", "", "", "1"
        ),
    )


class LogConfigurator(ngEOConfigConfigurator):
    section = "control"

    type_name = "logType"
    element_name = "log"

    parameters = (
        Parameter(
            str, "level", "Log level", "Log level, to determine which log "
            "types shall be logged.", "INFO", [
                ("DEBUG", "Log debug, info, warning and error messages"),
                ("INFO", "Log info, warning and error messages"),
                ("WARNING", "Log warning and error messages"),
                ("ERROR", "Log only error messages"),
                ("OFF", "Turn logging off")
            ]
        ),
    )


class ReportConfigurator(ngEOConfigConfigurator):
    section = "control"

    type_name = "reportsType"
    element_name = "reports"

    parameters = (
        Parameter(
            str, "report_store_dir", "Storage Directory",
            "Storage directory where automatically generated reports are "
            "stored.", "/var/www/ngeo/store/reports/"
        ),
    )


class NotificationConfigurator(ngEOConfigConfigurator):
    section = "control"

    type_name = "notificationType"
    element_name = "notification"

    parameters = (
        Parameter(
            str, "notification_url", "Notification URL",
            "URL to send the notification to.", ""
        ),
    )


class WebServerConfigurator(Configurator):
    type_name = "webServerType"
    element_name = "webServer"

    parameters = (
        Parameter(str, "baseurl", "Web Server base URL",
            "Base URL of the ngEO Web Server for authorization requests."
        ),
    )

    cmd_line_re = re.compile(".* (--baseurl|-b) (?P<url>[\S]*)")

    @lock_mapcache_config
    def set_values(self, baseurl):
        config = get_ngeo_config()
        root = read_mapcache_xml(config)
        try:
            template_elem = root.xpath("auth_method[1]/template")[0]
            template = template_elem.text
        except IndexError:
            pass  # no template given?

        match = self.cmd_line_re.match(template)
        if match:
            template = "".join((
                match.string[:match.start("url")],
                baseurl, match.string[match.end("url"):]
            ))
        else:
            template += " --baseurl %s" % baseurl
        template_elem.text = template

        write_mapcache_xml(root, config)

    @lock_mapcache_config
    def get_values(self):
        root = read_mapcache_xml(get_ngeo_config())
        try:
            template = root.xpath("auth_method[1]/template/text()")[0]
            baseurl = self.cmd_line_re.match(template).group("url")
        except (IndexError, AttributeError):
            baseurl = ""

        return {"baseurl": baseurl}


CONFIGURATORS = [
    IngestConfigurator(), CacheConfigurator(), LogConfigurator(),
    ReportConfigurator(), WebServerConfigurator(), NotificationConfigurator()
]


def get_configuration():
    return E("configuration", *[
        configurator.encode()
        for configurator in CONFIGURATORS
    ])


def get_schema():
    configurator_schema_types = [
        configurator.get_schema_type()
        for configurator in CONFIGURATORS
    ]

    parameter_schema_types = []
    for configurator in CONFIGURATORS:
        parameter_schema_types.extend(
            configurator.get_parameter_schema_types()
        )

    configuration_type = [
        XSD("complexType",
            XSD("sequence", *[
                configurator.get_schema_element()
                for configurator in CONFIGURATORS
            ]), name="configurationType"
        )
    ]

    return XSD("schema", *(
        configurator_schema_types
        + parameter_schema_types
        + configuration_type
        + [XSD("element", name="configuration", type="configurationType")]
    ))


def get_schema_and_configuration():
    return E("getConfigurationAndSchemaResponse",
        E("xsdSchema",
            get_schema()
        ),
        E("configurationData",
            get_configuration()
        )
    )


def get_config_revision():
    config = get_ngeo_config()
    return E("getConfigurationRevisionResponse",
        E("revision", str(safe_get(config, "config", "revision", 0)))
    )


def change_configuration(tree):
    config_elem = tree.find("configurationData/configuration")

    if config_elem is None:
        raise Exception("Invalid configuration provided.")

    for element in config_elem:
        tag = element.tag
        for configurator in CONFIGURATORS:
            if configurator.element_name == tag:
                break
        else:
            raise Exception("Invalid configuration element '%s' found." % tag)

        configurator.parse(element)

    write_ngeo_config()
