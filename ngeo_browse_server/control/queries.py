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

import os
import logging
import shutil
from datetime import datetime

from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.system import System
from eoxserver.resources.coverages.crss import fromShortCode
from eoxserver.resources.coverages.metadata import EOMetadata
from eoxserver.core.util.timetools import isotime

from ngeo_browse_server.config import models, get_ngeo_config
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.tasks import (
    seed_mapcache, add_mapcache_layer_xml, remove_mapcache_layer_xml
)
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config
from ngeo_browse_server.exceptions import NGEOException
from ngeo_browse_server.control.ingest.config import get_optimized_path

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
                  crs, replaced, footprint, num_bands, filename, 
                  seed_areas, config=None):
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
        try:
            models.NameValidator(browse.browse_identifier)
        except ValidationError, e:
            raise NGEOException("Browse Identifier '%s' not valid: '%s'." % 
                                (browse.browse_identifier, str(e.messages[0])),
                                "ValidationError")

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
        start_time__lte=browse.end_time, end_time__gte=browse.start_time,
        source=source
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
    
    seed_areas.append((minx, miny, maxx, maxy, start_time, end_time))
    
    return extent, (browse.start_time, browse.end_time)


def remove_browse(browse_model, browse_layer_model, coverage_id, 
                  seed_areas, config=None):
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
    
    try:
        time_model = mapcache_models.Time.objects.get(
            start_time__lte=browse_model.start_time,
            end_time__gte=browse_model.end_time,
            source__name=browse_layer_model.id
        )
    except DoesNotExist:
        # issue a warning if no corresponding Time object exists
        logger.warning("No MapCache Time object found for time: %s, %s" % (browse_model.start_time, browse_model.end_time))
    
    # unseed here
    try:
        seed_mapcache(tileset=browse_layer_model.id, grid=browse_layer_model.grid, 
                      minx=time_model.minx, miny=time_model.miny,
                      maxx=time_model.maxx, maxy=time_model.maxy, 
                      minzoom=browse_layer_model.lowest_map_level, 
                      maxzoom=browse_layer_model.highest_map_level,
                      start_time=time_model.start_time,
                      end_time=time_model.end_time,
                      delete=True,
                      **get_mapcache_seed_config(config))
    
    except Exception, e:
        logger.warn("Un-seeding failed: %s" % str(e))
    
    
    # approach
    #    - select the time model to which the browse refers
    #    - check if there are other browses within this time window
    #    - if yes:
    #        - split/shorten
    #        - for each new time:
    #            - save slot for seeding afterwards
    
    intersecting_browses_qs = models.Browse.objects.filter(
        start_time__lte = time_model.end_time,
        end_time__gte = time_model.start_time 
    )
    
    source_model = time_model.source
    time_model.delete()
    
    if len(intersecting_browses_qs):
        
        class Area(object):
            def __init__(self, minx, miny, maxx, maxy, start_time, end_time):
                self.minx = minx
                self.miny = miny
                self.maxx = maxx
                self.maxy = maxy
                self.start_time = start_time
                self.end_time = end_time
            
            def time_intersects(self, other):
                return (self.end_time >= other.start_time and
                        self.start_time <= other.end_time)
        
        # get "areas" with extent and time slice
        areas = []
        for browse in intersecting_browses_qs:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": browse.coverage_id}
            )
            minx, miny, maxx, maxy = coverage.getExtent()
            areas.append(Area(
                minx, miny, maxx, maxy, browse.start_time, browse.end_time
            ))

        # some helpers
        def intersects_with_group(area, group):
            for item in group:
                if area.time_intersects(item):
                    return True
            return False
        
        def merge_groups(first, *others):
            for other in others:
                for browse in other:
                    if browse not in first:
                        first.append(browse)
        
        groups = []
        
        # iterate over all browses that were associated with the deleted time
        for area in areas:
            to_be_merged = []
            
            if len(groups) == 0:
                groups.append([area])
                continue
            
            # check for intersections with other groups
            for group in groups:
                if intersects_with_group(area, group):
                    group.append(area)
                    to_be_merged.append(group)
            
            if len(to_be_merged):
                # actually perform the merge of the groups
                merge_groups(*to_be_merged)
                for group in to_be_merged[1:]:
                    groups.remove(group)
            
            else:
                groups.append([area])
        
        # each group needs to have its own Time model
        for group in groups:
            minx = group[0].minx
            miny = group[0].miny
            maxx = group[0].maxx
            maxy = group[0].maxy 
            start_time = group[0].start_time
            end_time = group[0].end_time
            
            for browse in group[1:]:
                minx = min(minx, browse.minx)
                miny = min(miny, browse.miny)
                maxx = max(maxx, browse.maxx)
                maxy = max(maxy, browse.maxy)
                start_time = min(start_time, browse.start_time)
                end_time = max(end_time, browse.end_time)
            
            # create time model
            time = mapcache_models.Time(
                minx=minx, miny=miny, maxx=maxx, maxy=maxy,
                start_time=start_time, end_time=end_time,
                source=source_model
            )
            time.full_clean()
            time.save()
            
            # add it to the regions that need to be seeded
            seed_areas.append((minx, miny, maxx, maxy, start_time, end_time))
    
    return replaced_extent, replaced_filename


def _create_model(browse, browse_report_model, browse_layer_model, coverage_id, model_cls):
    model = model_cls(browse_report=browse_report_model, browse_layer=browse_layer_model, 
                      coverage_id=coverage_id, **browse.get_kwargs())
    return model






"""

    <cache name="$LAYER_NAME" type="sqlite3">
        <dbfile>$MAPCACHE_DIR/$LAYER_NAME.sqlite</dbfile>
        <detect_blank>true</detect_blank>
    </cache>
    <source name="$LAYER_NAME" type="wms">
        <getmap>
            <params>
                <LAYERS>$LAYER_NAME</LAYERS>
                <TRANSPARENT>true</TRANSPARENT>
            </params>
        </getmap>
        <http>
            <url>http://localhost/browse/ows?</url>
        </http>
    </source>
    <tileset name="$LAYER_NAME">
        <source>$LAYER_NAME</source>
        <cache>$LAYER_NAME</cache>
        <grid max-cached-zoom="$HIGHEST_MAP_LEVEL" out-of-zoom-strategy="reassemble">$GRID_CACHE</grid>
        <format>mixed</format>
        <metatile>8 8</metatile>
        <expires>3600</expires>
        <read-only>true</read-only>
        <timedimension type="sqlite" default="2010">
            <dbfile>$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/data/mapcache.sqlite</dbfile>
            <query>select strftime('%Y-%m-%dT%H:%M:%SZ',start_time)||'/'||strftime('%Y-%m-%dT%H:%M:%SZ',end_time) from time where source_id=:tileset and start_time&lt;=datetime(:end_timestamp,'unixepoch') and end_time&gt;=datetime(:start_timestamp,'unixepoch') and maxx&gt;=:minx and maxy&gt;=:miny and minx&lt;=:maxx and miny&lt;=:maxy order by end_time desc limit 100</query>
        </timedimension>
    </tileset>
</mapcache>

"""


# browse layer management
def add_browse_layer(browse_layer, config=None):
    """ Add a browse layer to the ngEO Browse Server system. This includes the 
        database models, cache configuration and filesystem paths.
    """
    config = config or get_ngeo_config()

    try:
        # create a new browse layer model
        models.BrowseLayer.objects.create(**browse_layer.get_kwargs())

        # TODO related datasets

        # create EOxServer dataset series
        dss_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.dataset_series"
            }
        )
    except IntegrityError:
        raise

    dss_mgr.create(browse_layer.id,
        eo_metadata=EOMetadata(
            browse_layer.id,
            datetime.now(), datetime.now(), 
            MultiPolygon(Polygon.from_bbox((0, 0, 1, 1)))
        )
    )

    # remove source from mapcache sqlite
    mapcache_models.Source.objects.create(name=browse_layer.id)

    # add an XML section to the mapcache config xml
    add_mapcache_layer_xml(browse_layer, config)

    # create a base directory for optimized files
    directory = get_optimized_path("", browse_layer.id)
    if not os.path.exists(directory):
        os.makedirs(directory)


def update_browse_layer(browse_layer, config=None):
    config = config or get_ngeo_config()

    try:
        browse_layer_model = models.BrowseLayer.objects.get(id=browse_layer.id)
    except models.BrowseLayer.DoesNotExist:
        raise Exception("Could not update the previous browse layer")


    immutable_values = (
        "id", "browse_type", "contains_vertical_curtains", "r_band", "g_band",
        "b_band", "radiometric_interval_min", "radiometric_interval_max",
        "grid", "lowest_map_level", "highest_map_level", "strategy"
    )
    for key in immutable_values:
        if getattr(browse_layer_model, key) != getattr(browse_layer, key):
            raise Exception("Cannot change immutable property '%s'." % key)


    mutable_values = [
        "title", "description", "browse_access_policy", 
        "timedimension_default", "tile_query_limit"
    ]


    refresh_mapcache_xml = False
    for key in mutable_values:
        setattr(browse_layer_model, key, getattr(browse_layer, key))
        if key in ("timedimension_default", "tile_query_limit"):
            refresh_mapcache_xml = True

    # TODO related datasets

    browse_layer_model.full_clean()
    browse_layer_model.save()

    if refresh_mapcache_xml:
        remove_mapcache_layer_xml(browse_layer, config)
        add_mapcache_layer_xml(browse_layer, config)



def delete_browse_layer(browse_layer):
    # remove browse layer model. This should also delete all related browses 
    # and browse reports
    models.BrowseLayer.objects.get(id=browse_layer.id).delete()

    # remove source from mapcache sqlite
    mapcache_models.Source.objects.get(name=browse_layer.id).delete()

    # remove browse layer from mapcache XML
    remove_mapcache_layer_xml(browse_layer)

    # delete browse layer cache
    os.remove(get_tileset_path(browse_layer.browse_type))

    # delete all optimzed files by deleting the whole directory of the layer
    shutil.rmtree()
