#!/usr/bin/python

import os
import sys
import os.path
import json
import logging
import logging.handlers
import optparse
import datetime

parser = optparse.OptionParser(usage="usage: ./stac_export.py [OPTIONS]",
                               description="Exports browses to STAC items for import to VS. Contains default options which can be overwritten")
parser.add_option("-r", "--remove-path", dest="remove_path",
                  help="Part of path for data to remove. Defaults to: /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized",
                  default="/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized")
parser.add_option("-p", "--prepend-path", dest="prepend_path", default="/data",
                  help="Path to prepend to data paths. Defaults to: '/data'")
parser.add_option("-e", "--export-path", dest="export_path", default=os.getcwd(),
                  help="Export destination path. Defaults to current directory")
parser.add_option("-l", "--log-file", dest="log_file", default="",
                  help="Path to save stac export log to. Defaults to: ''")
parser.add_option("-L", "--limit", dest="limit", default=0,
                  help="Limits the queried browses to number specified. Defaults to 0 for no limit")
parser.add_option("-s", "--sys-path", dest="sys_path", 
                  default='/var/www/ngeo/ngeo_browse_server_instance',
                  help="Path to browse server instance. Defaults to: /var/www/ngeo/ngeo_browse_server_instance")
parser.add_option("-d", "--django-settings-module", dest="django_settings_module", 
                  default='ngeo_browse_server_instance.settings',
                  help="Path to django settings module. Defaults to: ngeo_browse_server_instance.settings")
parser.add_option("-c", "--collection", dest="collection", 
                  default='',
                  help="Collection to export. Defaults to '' for exporting all collections")
(options, _) = parser.parse_args()

LOG_FILE = options.log_file
REMOVE_PATH = options.remove_path
PREPEND_PATH = options.prepend_path
EXPORT_PATH = options.export_path
LIMIT = int(options.limit)
SYS_PATH = options.sys_path
DJANGO_SETTINGS_MODULE = options.django_settings_module
COLLECTION = options.collection

sys.path.append(SYS_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS_MODULE

from ngeo_browse_server.config.models import BrowseLayer, FootprintBrowse, Browse
from eoxserver.resources.coverages.models import LocalDataPackage, RectifiedDatasetRecord
from eoxserver.backends.models import LocalPath
from eoxserver.core.system import System

System.init()
LOGGER = logging.getLogger("stac_export")
FORMATTER = logging.Formatter("[%(asctime)s](%(name)s) - %(message)s")
LOGGER.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(FORMATTER)
LOGGER.addHandler(stream_handler)

if LOG_FILE:
    file_handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10 ** 6)
    file_handler.setFormatter(FORMATTER)
    LOGGER.addHandler(file_handler)


ITEM_MODEL = {
    "id": "",
    "type": "Feature",
    "stac_version": "1.0.0",
    "links": [],
    "stac_extensions": [],
    "geometry": {},
    "bbox": [],
    "properties": {},
    "assets": {},
    "collection": ""
}

COLLECTION_MODEL = {
    "id": "",
    "type": "Collection",
    "stac_version": "1.0.0",
    "description": "",
    "links": [],
    "stac_extensions": [],
    "extent": {},
    "license": "proprietary"
}
COMMON_COLLECTION_LINKS = [
    {
        "rel": "root",
        "href": "./catalog.json",
        "type": "application/json"
    },
    {
        "rel": "parent",
        "href": "./catalog.json",
        "type": "application/json"
    }
]

CATALOG_MODEL = {
        "id": "vs-catalog",
        "type": "Catalog",
        "stac_version": "1.0.0",
        "description": "A Browse server exported catalog",
        "links": [],
        "stac_extensions": [],
    }
COMMON_CATALOG_LINKS = [
    {
        "rel": "root",
        "href": "./catalog.json",
        "type": "application/json"
    },
]
DEFAULT_BEGIN = datetime.datetime(1990, 1, 1) 
DEFAULT_END = datetime.datetime(2030, 12, 31)
DEFAULT_BBOX = (-180, -85, 180, 85)   


def main():
    catalog = dict(CATALOG_MODEL)
    catalog_links = list(COMMON_CATALOG_LINKS)

    LOGGER.info("Starting export...")
    if COLLECTION:
        browse_layer = BrowseLayer.objects.get(id = COLLECTION)
        collections = [browse_layer]
        collection_count = 1
    else:
        collections = BrowseLayer.objects.all()
        collection_count = collections.count()

    for i, browse_layer in enumerate(collections, start=1):

        # create collection
        collection = dict(COLLECTION_MODEL)
        collection_name = str(browse_layer.browse_type)
        LOGGER.info('(%s/%s) Processing browse layer %s ' % (i, collection_count, collection_name))
        collection['id'] = collection_name
        collection['description'] = "%s collection" % collection_name
        eo_obj = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": collection_name}
        ) or System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": collection_name}
        )
        if eo_obj:
            bl_begin = eo_obj.getBeginTime()
            bl_end = eo_obj.getEndTime()
            bl_bbox = eo_obj.getFootprint().extent
        else:
            bl_begin = DEFAULT_BEGIN
            bl_end = DEFAULT_END
            bl_bbox = DEFAULT_BBOX
                     
        
        collection_extent = {
            "spatial": {
                "bbox": [
                    list(bl_bbox)
                ]
            },
            "temporal": {
                "interval": [
                    [   
                        bl_begin.strftime("%Y-%m-%dT%H:%M:%SZ"), 
                        bl_end.strftime("%Y-%m-%dT%H:%M:%SZ")
                     ]
                ]
            }
        }
        collection['extent'] = collection_extent
        collection_links = list(COMMON_COLLECTION_LINKS)
        catalog_links.append(
            {
                "rel": "child",
                "href": "./%s.json" % collection_name,
                "type": "application/json"
            }
        )

        browses = Browse.objects.filter(browse_layer = browse_layer)
        browses_count = LIMIT or browses.count()

        output_path = os.path.join(EXPORT_PATH, collection_name)
        if not os.path.exists(output_path):
            os.mkdir(output_path)

        for j, browse in enumerate(browses, start=1):
            # get browse
            rectified_record = RectifiedDatasetRecord.objects.get(eo_id = browse.coverage_id)
            id = str(browse.coverage_id)
            LOGGER.info('(%s/%s) Processing browse %s' % (j, browses_count, id))
            
            # prepare bbox
            extent_record = rectified_record.extent
            bbox = [
                extent_record.minx, 
                extent_record.miny, 
                extent_record.maxx, 
                extent_record.maxy
            ]


            # prepare footprint
            footprint = FootprintBrowse.objects.get(browse_ptr = browse)
            coords = footprint.coord_list
            x_coords = coords.split(" ")[::2]
            y_coords = coords.split(" ")[1::2]
            coords = [[float(x), float(y)] for x, y in zip(x_coords, y_coords)]

            # prepare datetime
            start = browse.start_time
            end = browse.end_time
            if start == end:
                datetime = {"datetime": start.isoformat()}
            else:
                datetime = {
                    "start_datetime": start.isoformat(), "end_datetime": end.isoformat()}        

            # prepare data path
            local_data_package = LocalDataPackage.objects.get(id = rectified_record.data_package_id)
            local_data_package_id = local_data_package.data_location_id
            path = LocalPath.objects.get(id = local_data_package_id).path
            data_path = str(path).replace(REMOVE_PATH, PREPEND_PATH)

            # create item
            item = dict(ITEM_MODEL)
            item['id'] = id
            item['bbox'] = bbox
            item['geometry'] = {
                "type": "Polygon",
                "coordinates": [coords]
            }
            item['collection'] = collection_name
            item['properties'] = datetime
            item['assets']['data'] = {
                "href": data_path, 
                "type": "image/tiff; application=geotiff"
            }

            # process links
            item_path = os.path.join(output_path, "%s.json" % id)
            collection_links.append(
                {
                    "rel": "item",
                    "href": os.path.relpath(item_path, EXPORT_PATH),
                    "type": "application/json"
                }
            )
            item_links = [
                {
                    "rel": "collection",
                    "href": "../%s.json" % collection_name,
                    "type": "application/json"
                },
                {
                    "rel": "parent",
                    "href": "../%s.json" % collection_name,
                    "type": "application/json"
                }
            ]         
            item['links'] = item_links

            # save item
            with open(item_path, 'w') as out_file:
                json.dump(item, out_file)

            if LIMIT and j == LIMIT:
                break

        # save collection
        collection['links'] = collection_links
        collection_path = os.path.join(EXPORT_PATH, "%s.json" % collection_name)
        with open(collection_path, 'w') as out_file:
            json.dump(collection, out_file)

    # save catalog
    catalog['links'] = catalog_links
    catalog_path = os.path.join(EXPORT_PATH, "catalog.json")
    with open(catalog_path, 'w') as out_file:
        json.dump(catalog, out_file)


if __name__ == "__main__":
    main()
