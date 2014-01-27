

from lxml import etree
from lxml.builder import ElementMaker, E

from ngeo_browse_server.config import get_ngeo_config, write_ngeo_config


ns_xsd_uri = "http://www.w3.org/2001/XMLSchema"
ns_xsd = lambda s: ("{%s}%s" % (ns_xsd_uri, s))
XSD = ElementMaker(namespace=ns_xsd_uri, nsmap={"xsd": ns_xsd_uri})

TYPE_MAP = {
    bool: (lambda s: s == "true")
}

ENCODE_MAP = {
    bool: (lambda b: "true" if b else "false")
}

SCHEMA_MAP = {
    bool: "boolean",
    int: "integer",
    str: "string",
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
                    ], base="string"
                ), name=self.type_name
            )

    def get_schema_element(self):
        return XSD("element",
            XSD("annotation", 
                XSD("label", self.title),
                XSD("tooltip", self.description)
            ),
            name=self.name, type=self.type_name
        )

    def parse(self, element):
        return TYPE_MAP.get(self.type, self.type)(element.text)

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
            if not value_element:
                raise ConfiguratorException("Element '%s/%s' not found" % (
                    self.type_name, parameter.name
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
        return XSD("complexType", *[
            parameter.get_schema_element()
            for parameter in self.parameters
        ], name=self.type_name)

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

        write_ngeo_config()


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
            int, "simplification_factor", "", 
            "Sets the factor for the simplification algorithm. See "
            "`http://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm` "
            "for details. Defaults to 2 (2 * resolution == 2 pixels) which "
            "provides reasonable results.", "2"
        ),
        Parameter(
            str, "threshold", "Merge time threshold", 
            "The maximum time difference between the two browse report to "
            "allow a 'merge'. E.g: 1w 5d 3h 12m 18ms. Defaults to '5h'.", "5h"
        ),
        Parameter(
            str, "strategy", "Ident browse strategy", 
            "Sets the 'strategy' for when an ingested browse is equal with an "
            "existing one. The 'merge'-strategy tries to merge the two "
            "existing images to one single. This is only possible if the time "
            "difference of the two browse reports (the report of the to be "
            "ingested browse and the one of the already existing one) is "
            "lower than the threshold. Otherwise a 'replace' is done. The "
            "'replace' strategy removes the previous browse, before ingesting "
            "the new one.", "merge"
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


CONFIGURATORS = [IngestConfigurator(), CacheConfigurator(), LogConfigurator()]


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
        )
    )

def get_schema_and_configuration():
    return E("getConfigurationAndSchemaResponse",
        E("xsdSchema",
            get_schema()
        ),
        E("configurationData",
            get_configuration()
        )
    )

