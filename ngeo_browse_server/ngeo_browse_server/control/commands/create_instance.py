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

"""Create a new ngEO Browse Server instance using the EOxServer 
create_instance command which will create a Django project with the instance 
name in the given (optional) directory.

"""

import shutil
import os, sys
from optparse import make_option

import eoxserver.core.commands.create_instance

import ngeo_browse_server
from ngeo_browse_server.control.management import ngEOBrowseServerAdminCommand

class Command(ngEOBrowseServerAdminCommand):
    option_list = ngEOBrowseServerAdminCommand.option_list + (                                             
        make_option('--id', nargs=1, action='store', metavar='INSTANCE_ID',
            help='Mandatory name of the ngEO Browse Server instance.'
        ),
        make_option('-d', '--dir', default='.', 
            help='Optional base directory. Defaults to the current directory.'
        ),
        make_option('--initial_data', metavar='filename', default=False,
            help='Location of the initial data. Must be in JSON format.'
        )
    )
    
    help = ("Creates a new ngEO Browse Server instance with all necessary "
            "files and folder structure.")
    args = ("--id INSTANCE_ID [--dir DIR --initial_data DIR --init_spatialite]")
    
    can_import_settings = False
    requires_model_validation = False
    
    def handle(self, *args, **options):
        instance_id = options['id']
        if instance_id is None:
            if len(args) == 1:
                instance_id = args[0]
            else:
                self.parser.error("Instance ID not given.")
    
        print("Started creation of ngEO Browse Server instance.")

        # create the initial eoxserver folder structure
        print("Initializing EOxServer project folder.")
        eoxserver.core.commands.create_instance.Command().execute(*args, **options)

        print("Finished creation of ngEO Browse Server instance.")
