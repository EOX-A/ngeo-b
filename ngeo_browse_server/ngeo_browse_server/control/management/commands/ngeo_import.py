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
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.core.system import System

from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.migration.imp import import_package


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--check-integrity', action="store_true",
            dest='check_integrity', default=False,
            help=("Only the integrity of the package and the compliance to this "
                  "server will be tested. No actual data is imported.")
        ),
        make_option('--ignore-cache', action="store_true",
            dest='ignore_cache', default=False,
            help=("If this option is set, the tile cache of the package will "
                  "be ignored and the tiles will be re-seeded after each "
                  "browse was imported.")
        )
    )
    
    args = ("[--check-integrity] [--ignore-cache] <package-path> ...")
    help = ("Imports the browse reports and browses from the given package(s). "
            "If cached tiles are present in the package aswell, those are "
            "inserted into the according tileset, but optionally the cache is "
            "also re-seeded.")

    def handle(self, *args, **kwargs):
        System.init()
        
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)
        
        package_paths = args
        if not len(package_paths):
            raise CommandError("No packages given.")
        
        check_integrity = kwargs["check_integrity"]
        ignore_cache = kwargs["ignore_cache"]
        
        config = get_ngeo_config()
        
        for package_path in package_paths:
            # TODO: handle each package in a transaction
            # TODO: create a transaction class that accumulates filenames to be 
            # deleted upon error
            
            import_package(package_path, check_integrity, ignore_cache, config)
