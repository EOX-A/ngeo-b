#!/usr/bin/python

import os
import sys
import os.path
import json
import logging
import logging.handlers
import optparse

parser = optparse.OptionParser(usage="usage: ./stac_export.py [OPTIONS]",
                               description="Exports browses to STAC items for import to VS. Contains default options which can be overwritten")
parser.add_option("-r", "--remove-path", dest="remove_path",
                  help="Part of path for data to remove. Defaults to: /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance",
                  default="/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance")
parser.add_option("-p", "--prepend-path", dest="prepend_path", default="",
                  help="Path to prepend to data paths. Defaults to: ''")
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


STAC_ITEM_MODEL = {
    "id": "",
    "type": "Feature",
    "stac_version": "1.0.0",
    "geometry": {},
    "bbox": [],
    "properties": {},
    "assets": {},
    "collection": "",
}


def main():
    LOGGER.info("Starting export...")
    if COLLECTION:
        collection = BrowseLayer.objects.get(id = COLLECTION)
        collections = [collection]
        collection_count = 1
    else:
        collections = BrowseLayer.objects.all()
        collection_count = collections.count()

    for i, collection in enumerate(collections, start=1):
        collection_name = str(collection.browse_type)
        LOGGER.info('(%s/%s) Processing collection %s ' % (i, collection_count, collection_name))

        browses = Browse.objects.filter(browse_layer = collection)
        browses_count = LIMIT or browses.count()

        output_path = os.path.join(EXPORT_PATH, collection_name)
        if not os.path.exists(output_path):
            os.mkdir(output_path)


        for j, browse in enumerate(browses, start=1):
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

            # prepare data path
            local_data_package = LocalDataPackage.objects.get(id = rectified_record.data_package_id)
            local_data_package_id = local_data_package.data_location_id
            path = LocalPath.objects.get(id = local_data_package_id).path
            data_path = str(path).replace(REMOVE_PATH, PREPEND_PATH)

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

            # create item
            item = dict(STAC_ITEM_MODEL)
            item['id'] = id
            item['bbox'] = bbox
            item['geometry'] = {
                "type": "Polygon",
                "coordinates": [coords]
            }
            item['collection'] = collection_name
            item['properties'] = datetime
            item['assets']['data'] = {
                "href": data_path, "type": "image/tiff; application=geotiff"}

            # save item
            json_path = os.path.join(output_path, "%s.json" % id)
            with open(json_path, 'w') as out_file:
                json.dump(item, out_file)

            if LIMIT and j == LIMIT:
                break


if __name__ == "__main__":
    main()
