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

from eoxserver.core.system import System
from eoxserver.resources.coverages.crss import fromShortCode
from eoxserver.resources.coverages.metadata import EOMetadata

from ngeo_browse_server.config import models
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.tasks import seed_mapcache
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config
from eoxserver.core.util.timetools import isotime


logger = logging.getLogger(__name__)

def get_existing_browse(browse, browse_layer_id):
    """ Get existing browse either via browse identifier if present or via 
        Start/End time in the same browse layer. """
    
    try:
        if browse.browse_identifier:
            try:
                return models.Browse.objects.get(
                    browse_identifier__value=browse.browse_identifier,
                    browse_layer__id=browse_layer_id
                )
            except models.Browse.DoesNotExist:
                pass
        return models.Browse.objects.get(
            start_time=browse.start_time,
            end_time=browse.end_time,
            browse_layer__id=browse_layer_id
        )
    except models.Browse.DoesNotExist:
        return None


def get_coverage_for_browse(browse):
    pass


def create_browse_report(browse_report, browse_layer_model):
    browse_report_model = models.BrowseReport(
        browse_layer=browse_layer_model, **browse_report.get_kwargs()
    )
    browse_report_model.full_clean()
    browse_report_model.save()
    return browse_report_model


def create_browse(browse, browse_report_model, browse_layer_model, coverage_id,
                  crs, replaced, footprint, num_bands, filename, config=None):
    """ Creates all required database models for the browse and returns the
        calculated extent of the registered coverage.
    """
    
    srid = fromShortCode(browse.reference_system_identifier)
    
    # create the correct model from the pared browse
    if browse.geo_type == "rectifiedBrowse":
        browse_model = _create_model(browse, browse_report_model, 
                                     browse_layer_model, coverage_id,
                                     models.RectifiedBrowse)
        browse_model.full_clean()
        browse_model.save()
        
    elif browse.geo_type == "footprintBrowse":
        browse_model = _create_model(browse, browse_report_model, 
                                    browse_layer_model, coverage_id,
                                    models.FootprintBrowse)
        browse_model.full_clean()
        browse_model.save()
        
    elif browse.geo_type == "regularGridBrowse":
        browse_model = _create_model(browse, browse_report_model, 
                                     browse_layer_model, coverage_id,
                                     models.RegularGridBrowse)
        browse_model.full_clean()
        browse_model.save()
        
        for coord_list in browse.coord_lists:
            coord_list = models.RegularGridCoordList(
                regular_grid_browse=browse_model, coord_list=coord_list
            )
            coord_list.full_clean()
            coord_list.save()
    
    elif browse.geo_type == "modelInGeotiffBrowse":
        browse_model = _create_model(browse, browse_report_model, 
                                     browse_layer_model, coverage_id,
                                     models.ModelInGeotiffBrowse)
        browse_model.full_clean()
        browse_model.save()
    
    else:
        raise NotImplementedError
    
    # if the browse contains an identifier, create the according model
    if browse.browse_identifier is not None:
        browse_identifier_model = models.BrowseIdentifier(
            value=browse.browse_identifier, browse=browse_model, 
            browse_layer=browse_layer_model
        )
        browse_identifier_model.full_clean()
        browse_identifier_model.save()
    
    # initialize the Coverage Manager for Rectified Datasets to register the
    # datasets in the database
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    
    # create EO metadata necessary for registration
    eo_metadata = EOMetadata(
        coverage_id, browse.start_time, browse.end_time, footprint
    )
    
    # get dataset series ID from browse layer, if available
    container_ids = []
    if browse_layer_model:
        container_ids.append(browse_layer_model.id)
    
    range_type_name = "RGB" if num_bands == 3 else "RGBA"
    
    # register the optimized dataset
    logger.info("Creating Rectified Dataset.")
    coverage = rect_mgr.create(obj_id=coverage_id, 
                               range_type_name=range_type_name,
                               default_srid=srid, visible=False, 
                               local_path=filename,
                               eo_metadata=eo_metadata, force=False, 
                               container_ids=container_ids)
    
    extent = coverage.getExtent()
    minx, miny, maxx, maxy = extent
    start_time, end_time = browse.start_time, browse.end_time
    
    # create mapcache models
    source, _ = mapcache_models.Source.objects.get_or_create(name=browse_layer_model.id)
    
    # search for time entries with the same time span
    times_qs = mapcache_models.Time.objects.filter(
        start_time__lte=browse.end_time, end_time__gte=browse.start_time
    )
    
    if len(times_qs) > 0:
        # If there are , merge them to one
        logger.info("Merging %d Time entries." % (len(times_qs) + 1))
        for time_model in times_qs:
            minx = min(minx, time_model.minx)
            miny = min(miny, time_model.miny)
            maxx = max(maxx, time_model.maxx)
            maxy = max(maxy, time_model.maxy)
            start_time = min(start_time, time_model.start_time)
            end_time = max(end_time, time_model.end_time)
            
            seed_mapcache(tileset=browse_layer_model.id, 
                          grid=browse_layer_model.grid, 
                          minx=time_model.minx, miny=time_model.miny,
                          maxx=time_model.maxx, maxy=time_model.maxy, 
                          minzoom=browse_layer_model.lowest_map_level, 
                          maxzoom=browse_layer_model.highest_map_level,
                          start_time=time_model.start_time,
                          end_time=time_model.end_time,
                          delete=True,
                          **get_mapcache_seed_config(config))
    
        logger.info("Result time span is %s/%s." % (isotime(start_time),
                                                    isotime(end_time)))
        times_qs.delete()
    
    time_model = mapcache_models.Time(start_time=start_time, end_time=end_time,
                                      minx=minx, miny=miny, 
                                      maxx=maxx, maxy=maxy,
                                      source=source)
    
    time_model.full_clean()
    time_model.save()
    
    return extent, (browse.start_time, browse.end_time)


def remove_browse(browse_model, browse_layer_model, coverage_id, config=None):
    """ Delete all models and caches associated with browse model. Image itself 
    is not deleted.
    Returns the extent and filename of the replaced image.
    """
    
    # get previous extent to "un-seed" MapCache in that area
    rect_ds = System.getRegistry().getFromFactory(
        "resources.coverages.wrappers.EOCoverageFactory",
        {"obj_id": browse_model.coverage_id}
    )
    replaced_extent = rect_ds.getExtent()
    replaced_filename = rect_ds.getData().getLocation().getPath()
    
    # delete the EOxServer rectified dataset entry
    rect_mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )
    rect_mgr.delete(obj_id=browse_model.coverage_id)
    browse_model.delete()
    
    # unseed here
    try:
        seed_mapcache(tileset=browse_layer_model.id, grid=browse_layer_model.grid, 
                      minx=replaced_extent[0], miny=replaced_extent[1],
                      maxx=replaced_extent[2], maxy=replaced_extent[3], 
                      minzoom=browse_layer_model.lowest_map_level, 
                      maxzoom=browse_layer_model.highest_map_level,
                      start_time=browse_model.start_time,
                      end_time=browse_model.end_time,
                      delete=True,
                      **get_mapcache_seed_config(config))
    
    except Exception, e:
        logger.warn("Un-seeding failed: %s" % str(e))
    
    
    # delete *one* of the fitting Time objects
    
    
    # TODO: 
    #  - get time entry for given browse
    #  - get all browses for given time entry
    #  - "unmerge" time objects if necessary
    
    mapcache_models.Time.objects.filter(
        start_time=browse_model.start_time,
        end_time=browse_model.end_time,
        source__name=browse_layer_model.id
    )[0].delete()
    
    return replaced_extent, replaced_filename


def _create_model(browse, browse_report_model, browse_layer_model, coverage_id, model_cls):
    model = model_cls(browse_report=browse_report_model, browse_layer=browse_layer_model, 
                      coverage_id=coverage_id, **browse.get_kwargs())
    return model
