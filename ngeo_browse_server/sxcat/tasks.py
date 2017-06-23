#------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2017 European Space Agency
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


class SxCatException(Exception):
    """ Base class for SxCat related errors. """


def add_collection(browse_layer):
    name = browse_layer.browse_type

    logger.info("Adding collection for '%s' to SxCat." % name)

    sxcat_coll_config = """\
[collection]
type = NRT
searchable_fields = beginAcquisition

[harvesting]
source = %s
#interval = P1D
#retry_time = PT15M
""" % browse_layer.harvesting_source

    # configure collection
    sxcat_config_args = [
        "sxcat", "config", name, "-i"
    ]
    logger.debug("SxCat configure collection command: '%s'. raw: '%s'."
                 % (" ".join(sxcat_config_args), sxcat_config_args))

    process = subprocess.Popen(sxcat_config_args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    out, err = process.communicate(input=sxcat_coll_config)
    for string in (out, err):
        for line in string.split("\n"):
            if line != '':
                logger.info("SxCat output: %s" % line)

    if process.returncode != 0:
        raise SxCatException("Collection configuring failed. Returncode '%d'."
                             % process.returncode)

    # enable harvesting
    sxcat_harvest_args = [
        "sxcat", "harvest", name
    ]
    logger.debug("SxCat enable harvesting command: '%s'. raw: '%s'."
                 % (" ".join(sxcat_harvest_args), sxcat_harvest_args))

    process = subprocess.Popen(sxcat_harvest_args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    out, err = process.communicate()
    for string in (out, err):
        for line in string.split("\n"):
            if line != '':
                logger.info("SxCat output: %s" % line)

    if process.returncode != 0:
        raise SxCatException("Harvest enabling failed. Returncode '%d'."
                             % process.returncode)

    logger.info("Successfully added collection to SxCat.")


def disable_collection(browse_layer):
    name = browse_layer.browse_type
    logger.info("Disabling harvesting for collection '%s' from SxCat." % name)

    # disable harvesting
    sxcat_args = [
        "sxcat", "harvest", "--purge", name
    ]
    logger.debug("SxCat disable harvesting command: '%s'. raw: '%s'."
                 % (" ".join(sxcat_args), sxcat_args))

    process = subprocess.Popen(sxcat_args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    out, err = process.communicate()
    for string in (out, err):
        for line in string.split("\n"):
            if line != '':
                logger.info("SxCat output: %s" % line)

    if process.returncode != 0:
        raise SxCatException("Disabling harvesting failed. Returncode '%d'."
                             % process.returncode)

    logger.info("Successfully disabled harvesting in SxCat.")


def remove_collection(browse_layer):
    name = browse_layer.browse_type
    logger.info("Removing collection for '%s' from SxCat." % name)

    # remove collection
    sxcat_args = [
        "sxcat", "remove", name
    ]
    logger.debug("SxCat remove collection command: '%s'. raw: '%s'."
                 % (" ".join(sxcat_args), sxcat_args))

    process = subprocess.Popen(sxcat_args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    out, err = process.communicate()
    for string in (out, err):
        for line in string.split("\n"):
            if line != '':
                logger.info("SxCat output: %s" % line)

    if process.returncode != 0:
        raise SxCatException("Removing collection failed. Returncode '%d'."
                             % process.returncode)

    logger.info("Successfully removed collection from SxCat.")
