#------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2017, 2018 European Space Agency
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#------------------------------------------------------------------------------

import logging
import subprocess

logger = logging.getLogger(__name__)

SXCAT_COLLECTION_CONF_TEMPLATE = """\
[collection]
type = NRT
searchable_fields = beginAcquisition

[harvesting]
source = {source}
{extra_config}
"""


class SxCatError(Exception):
    """ Base class for SxCat related errors. """


def add_collection(browse_layer):
    """ Create or update Sx-Cat collection and start periodic harvests. """

    collection_name = browse_layer.browse_type

    logger.info("Loading configuration for Sx-Cat collection '%s'.", collection_name)

    collection_conf = SXCAT_COLLECTION_CONF_TEMPLATE.format(
        source=_format_harvesting_source(browse_layer.harvesting_source),
        extra_config=browse_layer.harvesting_configuration.get("sxcat", "")
    )

    # create new or update existing collection configuration
    return_code = _sxcat_command(["config", collection_name, "-i"], collection_conf)
    if return_code != 0:
        raise SxCatError(
            "Loading of the Sx-Cat collection configuring failed. "
            "Returncode '%d'." % return_code
        )

    logger.info("Successfully loaded Sx-Cat collection configuration.")

    return_code = _sxcat_command(["harvest", collection_name])
    if return_code != 0:
        logger.warning(
            "Failed to schedule the Sx-Cat collection periodic harvest. "
            "Fix the problem and start the harvest manually by the "
            "'sxcat harvest %s' command.", collection_name
        )
    else:
        logger.info("Periodic harvest scheduled.")


def disable_collection(browse_layer):
    """ Clear Sx-Cat collection periodic harvests. """
    collection_name = browse_layer.browse_type
    logger.info("Disabling periodic harvests for Sx-Cat collection '%s'.", collection_name)

    return_code = _sxcat_command(["harvest", collection_name, '--purge'])
    if return_code != 0:
        logger.warning(
            "Failed to clear the scheduled harvests. "
            "Check the harvest scheduling by the 'sxcat info %s' command "
            "and, if necessary, run again 'sxcat harvest %s --purge' command.",
            collection_name, collection_name,
        )
    else:
        logger.info("Periodic harvest disabled.")


def remove_collection(browse_layer):
    """ Remove Sx-Cat collection. """
    collection_name = browse_layer.browse_type

    logger.info("Removing Sx-Cat collection '%s'.", collection_name)

    return_code = _sxcat_command(["remove", collection_name])
    if return_code != 0:
        logger.warning(
            "Failed to remove the Sx-Cat collection. "
            "Check if the collection exists by the 'sxcat info %s' command and, "
            "if so, remove the collection manually by the "
            "'sxcat remove %s' command.", collection_name, collection_name
        )
    else:
        logger.info("Successfully removed Sx-Cat collection.")


def _sxcat_command(sxcat_args, stdin=None):
    sxcat_args = ['sxcat'] + list(sxcat_args)

    logger.debug("Sx-Cat command: '%s' (%r)", " ".join(sxcat_args), sxcat_args)

    process = subprocess.Popen(
        sxcat_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        stdin=subprocess.PIPE
    )

    out, err = process.communicate(input=stdin)
    for string in (out, err):
        for line in string.split("\n"):
            if line:
                logger.info("Sx-Cat output: %s", line)

    return process.returncode


def _format_harvesting_source(source):
    if not source:
        return ""
    if isinstance(source, basestring):
        return source
    if len(source) == 1 and not source.keys()[0]:
        return source.values()[0]
    return "\n" + "\n".join(
        "    %s, %s" % item
        for item in source.items()
    )
