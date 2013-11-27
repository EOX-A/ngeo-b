#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Daniel Santillan <daniel.santillan@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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



from os.path import exists
from os import remove
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction 
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.core.system import System
from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.config.models import (BrowseLayer, Browse)
from ngeo_browse_server.mapcache.tasks import seed_mapcache
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config
from ngeo_browse_server.mapcache import models as mapcache_models



logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, CommandOutputMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--layer', '--browse-layer',
            dest='browse_layer_id',
            help=("The browse layer to be deleted.")
        ),
        make_option('--browse-type',
            dest='browse_type',
            help=("The browses of browse type to be deleted.")
        ),
        make_option('--start',
            dest='start',
            help=("The start date and time in ISO 8601 format.")
        ),
        make_option('--end',
            dest='end',
            help=("The end date and time in ISO 8601 format.")
        )
    )
    
    args = ("--layer=<layer-id> | --browse-type=<browse-type> "
            "[--start=<start-date-time>] [--end=<end-date-time>] " )
    help = ("Deletes the browses specified by either the layer ID "
            ", its browse type and optionally start and or end time" )

    def handle(self, *args, **kwargs):
        System.init()
        
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)
        
        browse_layer_id = kwargs.get("browse_layer_id")
        browse_type = kwargs.get("browse_type")
        if not browse_layer_id and not browse_type:
            raise CommandError("No browse layer or browse type was specified.")
        elif browse_layer_id and browse_type:
            raise CommandError("Both browse layer and browse type were specified.")
        
        start = kwargs.get("start")
        end = kwargs.get("end")
        
        
        # parse start/end if given
        if start: 
            start = getDateTime(start)
        if end:
            end = getDateTime(end)
        
        with transaction.commit_on_success():
            self._handle(start, end, browse_layer_id, browse_type)
            
    
    
    def _handle(self, start, end, browse_layer_id, browse_type):
            
        # query the browse layer
        if browse_layer_id:
            try:
                browse_layer_model = BrowseLayer.objects.get(id=browse_layer_id)
            except BrowseLayer.DoesNotExist:
                raise CommandError("Browse layer '%s' does not exist" % browse_layer_id)
        else:
            try:
                browse_layer_model = BrowseLayer.objects.get(browse_type=browse_type)
            except BrowseLayer.DoesNotExist:
                raise CommandError("Browse layer with browse type'%s' does "
                                       "not exist" % browse_type)
        
        
        # get all browses of browse layer
        browses_qs = Browse.objects.all().filter(browse_layer=browse_layer_model);
        
        # apply start/end filter
        if start and not end:
            browses_qs = browses_qs.filter(start_time__gte=start)
        elif end and not start:
            browses_qs = browses_qs.filter(end_time__lte=end)
        elif start and end:
            browses_qs = browses_qs.filter(start_time__gte=start, end_time__lte=end)
            
        paths_to_delete = []
        
        # go through all browses to be deleted
        for browse_model in browses_qs:
            
            coverage_wrapper = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": browse_model.coverage_id}
            )
            
            # save paths to optimized browse image
            data_package = coverage_wrapper.getData()
            data_package.prepareAccess()
            browse_file_path = data_package.getGDALDatasetIdentifier()
            paths_to_delete.append(browse_file_path)
            
            mgr = System.getRegistry().findAndBind(
                intf_id="resources.coverages.interfaces.Manager",
                params={
                    "resources.coverages.interfaces.res_type": "eo.rect_stitched_mosaic"
                }
            )
            
            
            replaced_extent = coverage_wrapper.getExtent()
                
            id_to_delete = browse_model.coverage_id
            
            # delete coverage      
            mgr.delete(browse_model.coverage_id)
            
            # delete browse          
            browse_model.delete()
            
            
            # unseed
            try:
                seed_mapcache(tileset=browse_layer_model.id, grid=browse_layer_model.grid, 
                    minx=replaced_extent[0], miny=replaced_extent[1],
                    maxx=replaced_extent[2], maxy=replaced_extent[3], 
                    minzoom=browse_layer_model.lowest_map_level, 
                    maxzoom=browse_layer_model.highest_map_level,
                    start_time=browse_model.start_time,
                    end_time=browse_model.end_time,
                    delete=True,
                    **get_mapcache_seed_config(None))
            except Exception, e:
                logger.warn("Un-seeding failed: %s" % str(e))
                
            mapcache_qs = mapcache_models.Time.objects.filter(
                start_time=browse_model.start_time,
                end_time=browse_model.end_time,
                source__name=browse_layer_model.id
            )
            import pdb;pdb.set_trace()
            # delete *one* of the fitting Time objects
            if len(mapcache_qs) > 0:
                mapcache_qs[0].delete()
            # issue a warning if no Time object exists
            else:
                logger.warning("No MapCache Time object found for time: %s, %s" % (browse_model.start_time, browse_model.end_time))
            
            logger.info("Coverage, browse and seed for id %s deleted."%id_to_delete) 
            
        
        # loop through optimized browse images and delete them
        # This is done at this point to make sure a rollback is possible
        # if there is an error while deleting the browses and coverages
        for file_path in paths_to_delete:
            if exists(file_path):
                remove(file_path)
                logger.info("Optimized browse image deleted: %s"%file_path) 
            else:
                logger.warning("Optimized browse image to be deleted not found in path: %s"%file_path)
        
        # TODO: 
        #   - think about what to do with brows report
        #   - think about what to do with cache
