#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 European Space Agency
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

import sys
from os import remove, makedirs, rmdir, environ
from os.path import (
    exists, dirname, join, isdir, samefile, commonprefix, abspath, relpath,
    basename
)
import shutil
from numpy import arange
import logging
import traceback
from datetime import datetime, timedelta as dt_timedelta
import string
import uuid
from urllib2 import urlopen, URLError, HTTPError
from math import copysign

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import URLValidator
from django.db import transaction
from django.template.loader import render_to_string
from eoxserver.core.system import System
from eoxserver.contrib import osr
from eoxserver.processing.gdal import reftools as rt
from eoxserver.processing.preprocessing import WMSPreProcessor, RGB, RGBA, ORIG_BANDS
from eoxserver.processing.preprocessing.format import get_format_selection
from eoxserver.processing.preprocessing.georeference import Extent, GeographicReference
from eoxserver.processing.preprocessing.util import (
    create_mem, copy_metadata
)
from eoxserver.resources.coverages.crss import fromShortCode, hasSwappedAxes
from eoxserver.resources.coverages.models import NCNameValidator
from eoxserver.processing.preprocessing.exceptions import GCPTransformException
from osgeo import gdal

from ngeo_browse_server.config import get_ngeo_config, safe_get
from ngeo_browse_server.config import models
from ngeo_browse_server.config.browsereport.decoding import (
    decode_browse_report, decode_coord_list, pairwise_iterative
)
from ngeo_browse_server.config.browsereport import data
from ngeo_browse_server.control.ingest.result import (
    IngestBrowseReportResult, IngestBrowseResult, IngestBrowseReplaceResult,
    IngestBrowseSkipResult, IngestBrowseFailureResult
)
from ngeo_browse_server.control.ingest.config import (
    get_project_relative_path, get_storage_path, get_optimized_path,
    get_format_config, get_optimization_config, get_ingest_config
)
from ngeo_browse_server.filetransaction import FileTransaction
from ngeo_browse_server.control.ingest.config import (
    get_success_dir, get_failure_dir
)
from ngeo_browse_server.control.ingest.exceptions import IngestionException
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.tasks import CRS_BOUNDS, seed_mapcache
from ngeo_browse_server.mapcache.config import get_mapcache_seed_config
from ngeo_browse_server.config.browsereport.serialization import (
    serialize_browse_report
)
from ngeo_browse_server.control.queries import (
    get_existing_browse, create_browse_report, create_browse, remove_browse
)
from ngeo_browse_server.control.ingest.preprocessing.preprocessor import (
    NGEOPreProcessor
)
from ngeo_browse_server.storage import get_file_manager


logger = logging.getLogger(__name__)
report_logger = logging.getLogger("ngEO-ingest")


#===============================================================================
# main functions
#===============================================================================

def ingest_browse_report(parsed_browse_report, do_preprocessing=True, config=None):
    """ Ingests a browse report. reraise_exceptions if errors shall be handled
    externally
    """

    # initialize the EOxServer system/registry/configuration
    System.init()

    try:
        # get the according browse layer
        browse_type = parsed_browse_report.browse_type
        browse_layer = models.BrowseLayer.objects.get(browse_type=browse_type)
    except models.BrowseLayer.DoesNotExist:
        logger.warn("Browse layer with browse type '%s' does not "
                    "exist." % parsed_browse_report.browse_type)
        raise IngestionException("Browse layer with browse type '%s' does not "
                                 "exist." % parsed_browse_report.browse_type)

    # generate a browse report model
    browse_report = create_browse_report(parsed_browse_report, browse_layer)

    # initialize the preprocessor with configuration values
    crs = None
    if browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible":
        crs = "EPSG:3857"
    elif browse_layer.grid == "urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad":
        crs = "EPSG:4326"

    logger.debug("Using CRS '%s' ('%s')." % (crs, browse_layer.grid))

    # create the required preprocessor/format selection
    format_selection = get_format_selection("GTiff",
                                            **get_format_config(config))
    logger.info("Format config %s" % get_format_config(config))

    if do_preprocessing:
        # add config parameters and custom params
        params = get_optimization_config(config)

        # add radiometric interval
        rad_min = browse_layer.radiometric_interval_min
        if rad_min is not None:
            params["radiometric_interval_min"] = rad_min
        else:
            rad_min = "min"
        rad_max = browse_layer.radiometric_interval_max
        if rad_max is not None:
            params["radiometric_interval_max"] = rad_max
        else:
            rad_max = "max"

        # add band selection
        if (browse_layer.r_band is not None and
            browse_layer.g_band is not None and
            browse_layer.b_band is not None):

            bands = [(browse_layer.r_band, rad_min, rad_max),
                     (browse_layer.g_band, rad_min, rad_max),
                     (browse_layer.b_band, rad_min, rad_max)]

            if params["bandmode"] == RGBA:
                # RGBA
                bands.append((0, 0, 0))

            params["bands"] = bands

        preprocessor = NGEOPreProcessor(format_selection, crs=crs, **params)
    else:
        preprocessor = None # TODO: CopyPreprocessor

    report_result = IngestBrowseReportResult()

    succeded = []
    failed = []

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    browse_dirname = _valid_path("%s_%s_%s_%s" % (
        browse_type, browse_report.responsible_org_name,
        browse_report.date_time.strftime("%Y%m%d%H%M%S%f"),
        timestamp
    ))
    success_dir = join(get_success_dir(config), browse_dirname)
    failure_dir = join(get_failure_dir(config), browse_dirname)

    if exists(success_dir):
        logger.warn("Success directory '%s' already exists.")
    else:
        makedirs(success_dir)
    if exists(failure_dir):
        logger.warn("Failure directory '%s' already exists.")
    else:
        makedirs(failure_dir)

    # Create a file manager, either local or a remote storage one
    manager = get_file_manager(config)

    # iterate over all browses in the browse report
    for parsed_browse in parsed_browse_report:
        # transaction management per browse
        with transaction.commit_manually():
            with transaction.commit_manually(using="mapcache"):
                try:
                    seed_areas = []
                    # try ingest a single browse and log success
                    result = ingest_browse(parsed_browse, browse_report,
                                           browse_layer, preprocessor, crs,
                                           success_dir, failure_dir,
                                           seed_areas, manager, config=config)

                    report_result.add(result)
                    succeded.append(parsed_browse)

                    # commit here to allow seeding
                    transaction.commit()
                    transaction.commit(using="mapcache")

                    logger.info("Committed changes to database.")

                    for minx, miny, maxx, maxy, start_time, end_time in seed_areas:
                        try:

                            # seed MapCache synchronously
                            # TODO: maybe replace this with an async solution
                            seed_mapcache(tileset=browse_layer.id,
                                          grid=browse_layer.grid,
                                          minx=minx, miny=miny,
                                          maxx=maxx, maxy=maxy,
                                          minzoom=browse_layer.lowest_map_level,
                                          maxzoom=browse_layer.highest_map_level,
                                          start_time=start_time,
                                          end_time=end_time,
                                          delete=False,
                                          **get_mapcache_seed_config(config))
                            logger.info("Successfully finished seeding.")

                        except Exception, e:
                            logger.warn("Seeding failed: %s" % str(e))

                    # log ingestions for report generation
                    # date/browseType/browseLayerId/start/end
                    report_logger.info("/\\/\\".join((
                        datetime.utcnow().isoformat("T") + "Z",
                        parsed_browse_report.browse_type,
                        browse_layer.id,
                        (parsed_browse.start_time.replace(tzinfo=None)-parsed_browse.start_time.utcoffset()).isoformat("T") + "Z",
                        (parsed_browse.end_time.replace(tzinfo=None)-parsed_browse.end_time.utcoffset()).isoformat("T") + "Z"
                    )))

                except Exception, e:
                    # report error
                    logger.error("Failure during ingestion of browse '%s'." %
                                 parsed_browse.browse_identifier)
                    logger.error("Exception was '%s': %s" % (type(e).__name__, str(e)))
                    logger.debug(traceback.format_exc() + "\n")

                    # undo latest changes, append the failure and continue
                    report_result.add(IngestBrowseFailureResult(
                        parsed_browse.browse_identifier,
                        getattr(e, "code", None) or type(e).__name__, str(e))
                    )
                    failed.append(parsed_browse)

                    transaction.rollback()
                    transaction.rollback(using="mapcache")

    # generate browse report and save to to success/failure dir
    if len(succeded):
        try:
            logger.info("Creating browse report for successfully ingested "
                        "browses at '%s'." % success_dir)
            succeded_report = data.BrowseReport(
                parsed_browse_report.browse_type,
                parsed_browse_report.date_time,
                parsed_browse_report.responsible_org_name,
                succeded
            )
            _save_result_browse_report(succeded_report, success_dir)

        except Exception, e:
            logger.warn("Could not write result browse report as the file '%s'.")
    else:
        try:
            rmdir(success_dir)
        except Exception, e:
            logger.warn("Could not remove the unused dir '%s'." % success_dir)


    if len(failed):
        try:
            logger.info("Creating browse report for erroneously ingested "
                        "browses at '%s'." % failure_dir)
            failed_report = data.BrowseReport(
                parsed_browse_report.browse_type,
                parsed_browse_report.date_time,
                parsed_browse_report.responsible_org_name,
                failed
            )
            _save_result_browse_report(failed_report, failure_dir)

        except Exception, e:
            logger.warn("Could not write result browse report as the file '%s'.")
    else:
        try:
            rmdir(failure_dir)
        except Exception, e:
            logger.warn("Could not remove the unused dir '%s'." % failure_dir)


    return report_result


def ingest_browse(parsed_browse, browse_report, browse_layer, preprocessor, crs,
                  success_dir, failure_dir, seed_areas, manager, config=None):
    """ Ingests a single browse report, performs the preprocessing of the data
    file and adds the generated browse model to the browse report model. Returns
    a boolean value, indicating whether or not the browse has been inserted or
    replaced a previous browse entry.
    """

    logger.info("Ingesting browse '%s'."
                % (parsed_browse.browse_identifier or "<<no ID>>"))

    replaced = False
    replaced_extent = None
    replaced_filename = None
    merge_with = None
    merge_footprint = None

    config = config or get_ngeo_config()

    coverage_id = parsed_browse.browse_identifier
    if not coverage_id:
        # no identifier given, generate a new one
        coverage_id = _generate_coverage_id(parsed_browse, browse_layer)
        logger.info("No browse identifier given, generating coverage ID '%s'."
                    % coverage_id)
    else:
        coverage_id = browse_layer.id + "_" + coverage_id
        try:
            NCNameValidator(coverage_id)
        except ValidationError:
            # given ID is not valid, generate a new identifier
            old_id = coverage_id
            coverage_id = _generate_coverage_id(parsed_browse, browse_layer)
            logger.info("Browse ID '%s' is not a valid coverage ID. Using "
                        "generated ID '%s'." % (old_id, coverage_id))

    # get the `leave_original` setting
    leave_original = False
    try:
        leave_original = config.getboolean("control.ingest", "leave_original")
    except:
        pass

    # shorten browse time by percentage of interval if configured
    shorten_ingested_interval_percent = browse_layer.shorten_ingested_interval
    if shorten_ingested_interval_percent is not None and shorten_ingested_interval_percent != 0.0:
        delta = parsed_browse.end_time - parsed_browse.start_time

        # because python 2.6 does not have timedelta.total_seconds()
        delta_in_seconds = (delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10**6) / float(10**6)
        delta_add_subtract = dt_timedelta(seconds=(delta_in_seconds * shorten_ingested_interval_percent / 200.0))
        updated_start_time = parsed_browse.start_time + delta_add_subtract
        # round to seconds because of mapcache
        if updated_start_time.microsecond >= 500000:
            updated_start_time = updated_start_time + dt_timedelta(seconds=1)
        updated_start_time = updated_start_time.replace(microsecond=0)
        parsed_browse.set_start_time(updated_start_time)
        if shorten_ingested_interval_percent == 100.0:
            # to be sure that no wierd micro-second rounding happens
            parsed_browse.set_end_time(updated_start_time)
        else:
            # round to seconds because of mapcache
            updated_end_time = parsed_browse.end_time - delta_add_subtract
            if updated_end_time.microsecond >= 500000:
                updated_end_time = updated_end_time + datetime.timedelta(seconds=1)
            updated_end_time = updated_end_time.replace(microsecond=0)
            parsed_browse.set_end_time(updated_end_time)

    # get the input and output filenames
    storage_path = get_storage_path()
    # if file_name is a URL download browse first and store it locally
    validate = URLValidator()
    try:
        validate(parsed_browse.file_name)
        input_filename = abspath(get_storage_path(
            basename(parsed_browse.file_name), config=config))
        logger.info("URL given, downloading browse image from '%s' to '%s'."
                    % (parsed_browse.file_name, input_filename))
        if not exists(input_filename):
            try:
                remote_browse = urlopen(parsed_browse.file_name)
                with open(input_filename, "wb") as local_browse:
                    local_browse.write(remote_browse.read())
            except HTTPError, e:
                raise IngestionException("HTTP error downloading '%s': %s"
                                         % (parsed_browse.file_name, e.code))
            except URLError, e:
                raise IngestionException("URL error downloading '%s': %s"
                                         % (parsed_browse.file_name, e.reason))
        else:
            raise IngestionException("File do download already exists locally "
                                     "as '%s'" % input_filename)

    except ValidationError:
        input_filename = abspath(get_storage_path(parsed_browse.file_name,
                                                  config=config))
        logger.info("Filename given, using local browse image '%s'."
                    % input_filename)

    # check that the input filename is valid -> somewhere under the storage dir
    if commonprefix((input_filename, storage_path)) != storage_path:
        raise IngestionException("Input path '%s' points to an invalid "
                                 "location." % parsed_browse.file_name)
    try:
        models.FileNameValidator(input_filename)
    except ValidationError, e:
        raise IngestionException("%s" % str(e), "ValidationError")

    # Get filename to store preprocessed image
    output_filename = "%s_%s" % (
        uuid.uuid4().hex, basename(parsed_browse.file_name)
    )
    output_filename = _valid_path(
        get_optimized_path(
            output_filename, browse_layer.id + "/" +
            str(parsed_browse.start_time.year), config=config
        )
    )
    output_filename = preprocessor.generate_filename(output_filename)

    try:
        ingest_config = get_ingest_config(config)

        # check if a browse already exists and decide how to deal with it
        existing_browse_model = get_existing_browse(
            parsed_browse.browse_identifier, coverage_id, browse_layer.id)

        if existing_browse_model:
            previous_time = existing_browse_model.browse_report.date_time
            current_time = browse_report.date_time
            timedelta = current_time - previous_time

            # get strategy and merge threshold
            threshold = ingest_config["merge_threshold"]
            if browse_layer.strategy != "inherit":
                strategy = browse_layer.strategy
            else:
                strategy = ingest_config["strategy"]

            if strategy == "merge" and timedelta < threshold:

                if previous_time > current_time:
                    # TODO: raise exception?
                    pass

                rect_ds = System.getRegistry().getFromFactory(
                    "resources.coverages.wrappers.EOCoverageFactory",
                    {"obj_id": existing_browse_model.coverage_id}
                )
                merge_footprint = rect_ds.getFootprint()
                merge_with = rect_ds.getData().getLocation().getPath()

                replaced_time_interval = (existing_browse_model.start_time,
                                          existing_browse_model.end_time)

                _, _ = remove_browse(
                    existing_browse_model, browse_layer, coverage_id,
                    seed_areas, config=config
                )
                replaced = False
                logger.debug("Existing browse found, merging it.")

            elif strategy == "skip" and current_time <= previous_time:
                logger.debug("Existing browse found and not older, skipping.")
                return IngestBrowseSkipResult(parsed_browse.browse_identifier)

            else:
                # perform replacement

                replaced_time_interval = (existing_browse_model.start_time,
                                          existing_browse_model.end_time)

                replaced_extent, replaced_filename = remove_browse(
                    existing_browse_model, browse_layer, coverage_id,
                    seed_areas, config=config
                )
                replaced = True
                logger.info("Existing browse found, replacing it.")

        else:
            # A browse with that identifier does not exist, so create a new one
            logger.info("Creating new browse.")

        replaced_filename_remote = None
        if replaced_filename and replaced_filename.startswith('/vsiswift'):
            # TODO: delete if everything went okay
            replaced_filename_remote = replaced_filename
            replaced_filename = None

        merge_with_remote = None
        if merge_with and merge_with.startswith('/vsiswift'):
            merge_with_remote = merge_with
            # TODO: get local path
            merge_with = "/tmp/merge_%s_%s" % (
                uuid.uuid4().hex, basename(parsed_browse.file_name)
            )
            manager.download_file(merge_with_remote, merge_with)

        # assert that the output file does not exist (unless it is a to-be
        # replaced file).
        if (exists(output_filename) and
            ((replaced_filename and
              not samefile(output_filename, replaced_filename))
             or not replaced_filename)):
            raise IngestionException("Output file '%s' already exists and is "
                                     "not to be replaced." % output_filename)

        # wrap all file operations with IngestionTransaction
        with FileTransaction((output_filename, replaced_filename)):
            with FileTransaction((merge_with,), True):
                # assert that the input file exists
                if not exists(input_filename):
                    raise IngestionException("Input file '%s' does not exist."
                                             % input_filename)

                clipping = None
                if (parsed_browse.geo_type == "regularGridBrowse" and
                    ingest_config["regular_grid_clipping"]) or \
                    (parsed_browse.geo_type == "footprintBrowse" and
                     ("ncol" in parsed_browse.col_row_list or
                      "nrow" in parsed_browse.col_row_list)):
                    clipping = _get_clipping(input_filename)

                # initialize a GeoReference for the preprocessor
                geo_reference = _georef_from_parsed(parsed_browse, clipping)

                # check that the output directory exists
                safe_makedirs(dirname(output_filename))

                # start the preprocessor
                logger.info("Starting preprocessing on file '%s' to create '%s'."
                            % (input_filename, output_filename))

                try:
                    result = preprocessor.process(
                        input_filename, output_filename, geo_reference,
                        True, merge_with, merge_footprint
                    )
                except (RuntimeError, GCPTransformException), e:
                    raise IngestionException, str(e), sys.exc_info()[2]

                # validate preprocess result
                if result.num_bands not in (1, 3, 4):  # color index, RGB, RGBA
                    raise IngestionException("Processed browse image has %d bands."
                                             % result.num_bands)

                if manager:
                    prefix = join(
                        browse_layer.id, str(parsed_browse.start_time.year)
                    )

                    manager.upload_file(prefix, output_filename)
                    remove(output_filename)

                    manager.prepare_environment()

                    filename = basename(output_filename)
                    output_filename = manager.get_vsi_filename(
                        "%s/%s" % (prefix, filename)
                    )

                logger.info("Creating database models.")
                extent, time_interval = create_browse(
                    parsed_browse, browse_report, browse_layer, coverage_id,
                    crs, replaced, result.footprint_geom, result.num_bands,
                    output_filename, seed_areas, config=config
                )

    except:
        # save exception info to re-raise it
        exc_info = sys.exc_info()

        logger.error("Error during ingestion of Browse '%s'. Moving "
                     "original image to `failure_dir` '%s'."
                     % (parsed_browse.browse_identifier, failure_dir))

        # move the file to failure folder
        try:
            if not leave_original:
                storage_dir = get_storage_path()
                relative = relpath(input_filename, storage_dir)
                dst_dirname = join(failure_dir, dirname(relative))
                safe_makedirs(dst_dirname)
                shutil.move(input_filename, dst_dirname)
        except Exception, e:
            logger.warn("Could not move '%s' to configured "
                        "`failure_dir` '%s'. Error was: '%s'."
                        % (input_filename, failure_dir, str(e)))

        # re-raise the exception
        raise exc_info[0], exc_info[1], exc_info[2]

    else:
        if merge_with_remote:
            try:
                manager.delete_file(merge_with_remote)
            except Exception as e:
                logger.warn(
                    "Unable to delete merged file on swift storage '%s'. "
                    "Error was: '%s'"
                    % (replaced_filename_remote, e)
                )

        if replaced_filename_remote:
            try:
                manager.delete_file(replaced_filename_remote)
            except Exception as e:
                logger.warn(
                    "Unable to delete replaced file on swift storage '%s'. "
                    "Error was: '%s'"
                    % (replaced_filename_remote, e)
                )

        # move the file to success folder, or delete it right away
        delete_on_success = True
        try:
            delete_on_success = config.getboolean(
                "control.ingest", "delete_on_success"
            )
        except:
            pass

        if not leave_original:
            if delete_on_success:
                remove(input_filename)
            else:
                try:
                    storage_dir = get_storage_path()
                    relative = relpath(input_filename, storage_dir)
                    dst_dirname = join(success_dir, dirname(relative))
                    safe_makedirs(dst_dirname)
                    shutil.move(input_filename, dst_dirname)
                except Exception, e:
                    logger.warn("Could not move '%s' to configured "
                                "`success_dir` '%s'. Error was: '%s'."
                                % (input_filename, success_dir, str(e)))

    logger.info("Successfully ingested browse with coverage ID '%s'."
                % coverage_id)

    if not replaced:
        return IngestBrowseResult(parsed_browse.browse_identifier, extent,
                                  time_interval)

    else:
        return IngestBrowseReplaceResult(parsed_browse.browse_identifier,
                                         extent, time_interval, replaced_extent,
                                         replaced_time_interval)


#===============================================================================
# helper functions
#===============================================================================

def safe_makedirs(path):
    """ make dirs without raising an exception when the directories are already
    existing.
    """

    if not exists(path):
        makedirs(path)


def _get_clipping(path):
    ds = gdal.Open(path)
    return ds.RasterXSize, ds.RasterYSize


def _georef_from_parsed(parsed_browse, clipping=None):
    srid = fromShortCode(parsed_browse.reference_system_identifier)

    if (parsed_browse.reference_system_identifier == "RAW" and
        parsed_browse.geo_type != "modelInGeotiffBrowse"):
        raise IngestionException("Given referenceSystemIdentifier '%s' not "
                                 "valid for a '%s'."
                                 % (parsed_browse.reference_system_identifier,
                                    parsed_browse.geo_type))

    if srid is None and parsed_browse.reference_system_identifier != "RAW":
        raise IngestionException("Given referenceSystemIdentifier '%s' not valid."
                                 % parsed_browse.reference_system_identifier)

    swap_axes = hasSwappedAxes(srid)

    if parsed_browse.geo_type == "rectifiedBrowse":
        coords = decode_coord_list(parsed_browse.coord_list, swap_axes)
        # values are for bottom/left and top/right pixel
        coords = [coord for pair in coords for coord in pair]
        assert(len(coords) == 4)
        return Extent(*coords, srid=srid)

    elif parsed_browse.geo_type == "footprintBrowse":
        # Generate GCPs from footprint coordinates
        pixels = decode_coord_list(parsed_browse.col_row_list)
        # substitute ncol and nrow with image size
        if clipping:
            clip_x, clip_y = clipping
            pixels[:] = [(clip_x if x == "ncol" else x, clip_y if y == "nrow"
                         else y) for x, y in pixels]
        coord_list = decode_coord_list(parsed_browse.coord_list, swap_axes)

        if _coord_list_crosses_dateline(coord_list, CRS_BOUNDS[srid]):
            logger.info("Footprint crosses the dateline. Normalizing it.")
            coord_list = _unwrap_coord_list(coord_list, CRS_BOUNDS[srid])

        assert(len(pixels) == len(coord_list))
        gcps = [(x, y, pixel, line)
                for (x, y), (pixel, line) in zip(coord_list, pixels)]


        # check that the last point of the footprint is the first
        if not gcps[0] == gcps[-1]:
            raise IngestionException("The last value of the footprint is not "
                                     "equal to the first.")
        gcps.pop()

        return GCPList(gcps, srid)

    elif parsed_browse.geo_type == "regularGridBrowse":
        # calculate a list of pixel coordinates according to the values of the
        # parsed browse report (col_node_number * row_node_number)
        range_x = arange(
            0.0, parsed_browse.row_node_number * parsed_browse.row_step,
            parsed_browse.row_step
        )
        range_y = arange(
            0.0, parsed_browse.col_node_number * parsed_browse.col_step,
            parsed_browse.col_step
        )
        pixels = [(x, y) for x in range_x for y in range_y]

        # apply clipping
        if clipping:
            clip_x, clip_y = clipping
            pixels[:] = [
                (min(clip_x, x), min(clip_y, y)) for x, y in pixels
            ]

        # decode coordinate lists and check if any crosses the dateline
        coord_lists = []
        crosses_dateline = False
        for coord_list in parsed_browse.coord_lists:
            coord_list = decode_coord_list(coord_list, swap_axes)

            crosses_dateline = crosses_dateline or \
                _coord_list_crosses_dateline(coord_list, CRS_BOUNDS[srid])
            coord_lists.append(coord_list)

        # if any coordinate list was crossing the dateline, unwrap all
        # coordinate lists
        if crosses_dateline:
            logger.info("Regular grid crosses the dateline. Normalizing it.")

            # unwrap each coordinate list individually
            coord_lists = [
                _unwrap_coord_list(coord_list, CRS_BOUNDS[srid])
                for coord_list in coord_lists
            ]

            full = float(CRS_BOUNDS[srid][2] - CRS_BOUNDS[srid][0])
            half = full / 2

            # unwrap the list of coordinate lists
            x_last = coord_lists[0][0][0]
            i = 1
            for coord_list in coord_lists[1:]:
                if abs(x_last - coord_list[0][0]) > half:
                    coord_lists[i] = [(x - full * copysign(1, x), y) for (x, y) in coord_list]
                x_last = coord_lists[i][0][0]
                i += 1

            # Make sure unwrapped_coord_lists stays within CRS_BOUNDS[srid][0]
            # to CRS_BOUNDS[srid][2] + full, for EPSG:4326 -180 to 540.
            maxx = max(max((x for (x, y) in coord_list) for coord_list in coord_lists))
            minx = min(min((x for (x, y) in coord_list) for coord_list in coord_lists))
            if maxx > (CRS_BOUNDS[srid][2] + full) or minx < CRS_BOUNDS[srid][0]:
                raise IngestionException("Footprint too huge to unwrap.")

        coords = []
        for coord_list in coord_lists:
            coords.extend(coord_list)

        # check validity of regularGrid
        if len(parsed_browse.coord_lists) != parsed_browse.row_node_number:
            raise IngestionException("Invalid regularGrid: number of coordinate "
                                     "lists is not equal to the given row node "
                                     "number.")

        elif len(coords) / len(parsed_browse.coord_lists) != parsed_browse.col_node_number:
            raise IngestionException("Invalid regularGrid: number of coordinates "
                                     "does not fit given columns number.")

        gcps = [(x, y, pixel, line)
                for (x, y), (pixel, line) in zip(coords, pixels)]
        return GCPList(gcps, srid)

    elif parsed_browse.geo_type == "modelInGeotiffBrowse":
        return None

    else:
        raise NotImplementedError("Invalid geo-reference type '%s'."
                                  % parsed_browse.geo_type)


def _generate_coverage_id(parsed_browse, browse_layer):
    frmt = "%Y%m%d%H%M%S%f"
    return "%s_%s_%s_%s" % (browse_layer.id,
                            parsed_browse.start_time.strftime(frmt),
                            parsed_browse.end_time.strftime(frmt),
                            parsed_browse.file_name)


def _save_result_browse_report(browse_report, path):
    "Render the browse report to the template and save it under the given path."

    if isdir(path):
        # generate a filename
        path = join(path, _valid_path("%s_%s_%s_%s.xml" % (
            browse_report.browse_type, browse_report.responsible_org_name,
            browse_report.date_time.strftime("%Y%m%d%H%M%S%f"),
            datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        )))

    if exists(path):
        logger.warn("Could not write result browse report as the file '%s' "
                    "already exists.")
        return

    safe_makedirs(dirname(path))

    with open(path, "w+") as f:
        serialize_browse_report(browse_report, f)


FILENAME_CHARS = "/_-." + string.ascii_letters + string.digits


def _valid_path(filename):
    return ''.join(c for c in filename if c in FILENAME_CHARS)


def _coord_list_crosses_dateline(coord_list, bounds):
    """ Helper function to check whether or not a coord list crosses the
    dateline or anti meridian. Checked via iterating through connections of
    points and testing if west-east distance is above half of the full CRS
    distance, for EPSG:4326 180 deg.
    """

    half = float((bounds[2] - bounds[0]) / 2)
    for (x1, _), (x2, _) in pairwise_iterative(coord_list):
        if abs(x1 - x2) > half:
            return True

    return False


def _unwrap_coord_list(coord_list, bounds):
    """ 'Unwraps' a coordinate list that crosses the dateline. """

    full = float(bounds[2] - bounds[0])
    half = full / 2

    # Iterate through coordinates and unwrap if west-east distance to previous
    # one is above half of the full CRS distance, for EPSG:4326 180 deg.
    unwrapped_coord_list = [coord_list[0]]
    x_last = coord_list[0][0]
    for (x, y) in coord_list[1:]:
        if abs(x_last - x) > half:
            x -= full * copysign(1, x)
        x_last = x
        unwrapped_coord_list.append((x, y))

    # Make sure unwrapped_coord_list stays within bounds[0] to bounds[2] +
    # full, for EPSG:4326 -180 to 540.
    maxx = max(x for (x, y) in unwrapped_coord_list)
    minx = min(x for (x, y) in unwrapped_coord_list)
    if maxx > (bounds[2] + full) and minx >= bounds[2]:
        unwrapped_coord_list = [(x - full, y) for (x, y) in unwrapped_coord_list]
    elif minx < bounds[0] and maxx <= bounds[2]:
        unwrapped_coord_list = [(x + full, y) for (x, y) in unwrapped_coord_list]
    elif maxx > (bounds[2] + full) or minx < bounds[0]:
        raise IngestionException("Footprint too huge to unwrap.")

    return unwrapped_coord_list


class GCPList(GeographicReference):
    """ Sets a list of GCPs (Ground Control Points) to the dataset and then
        performs a rectification to a projection specified by SRID.
    """

    def __init__(self, gcps, gcp_srid=4326, srid=None):
        """ Expects a list of GCPs as a list of tuples in the form
            'x,y,[z,]pixel,line'.
        """

        self.gcps = map(lambda gcp: gdal.GCP(*gcp) if len(gcp) == 5
                        else gdal.GCP(gcp[0], gcp[1], 0.0, gcp[2], gcp[3]),
                        gcps)
        self.gcp_srid = gcp_srid
        self.srid = srid


    def apply(self, src_ds):
        # setup
        dst_sr = osr.SpatialReference()
        gcp_sr = osr.SpatialReference()

        dst_sr.ImportFromEPSG(self.srid if self.srid is not None
                              else self.gcp_srid)
        gcp_sr.ImportFromEPSG(self.gcp_srid)


        logger.debug("Using GCP Projection '%s'" % gcp_sr.ExportToWkt())
        logger.debug("Applying GCPs: MULTIPOINT(%s) -> MULTIPOINT(%s)"
                      % (", ".join([("(%f %f)") % (gcp.GCPX, gcp.GCPY) for gcp in self.gcps]) ,
                      ", ".join([("(%f %f)") % (gcp.GCPPixel, gcp.GCPLine) for gcp in self.gcps])))
        # set the GCPs
        src_ds.SetGCPs(self.gcps, gcp_sr.ExportToWkt())

        # Try to find and use the best transform method/order.
        # Orders are: -1 (TPS), 3, 2, and 1 (all GCP)
        # Loop over the min and max GCP number to order map.
        for min_gcpnum, max_gcpnum, order in [(3, None, -1), (10, None, 3), (6, None, 2), (3, None, 1)]:
            # if the number of GCP matches
            if len(self.gcps) >= min_gcpnum and (max_gcpnum is None or len(self.gcps) <= max_gcpnum):
                try:

                    if (order < 0):
                        # try TPS
                        rt_prm = {"method": rt.METHOD_TPS, "order": 1}
                    else:
                        # use the polynomial GCP interpolation as requested
                        rt_prm = {"method": rt.METHOD_GCP, "order": order}

                    logger.debug("Trying order '%i' {method:%s,order:%s}" % \
                        (order, rt.METHOD2STR[rt_prm["method"]] , rt_prm["order"] ) )
                    # get the suggested pixel size/geotransform
                    size_x, size_y, geotransform = rt.suggested_warp_output(
                        src_ds,
                        None,
                        dst_sr.ExportToWkt(),
                        **rt_prm
                    )
                    if size_x > 100000 or size_y > 100000:
                        raise RuntimeError(
                            "Calculated size of '%i x %i' exceeds limit of "
                            "'100000 x 100000'." % (size_x, size_y)
                        )
                    logger.debug("New size is '%i x %i'" % (size_x, size_y))

                    # create the output dataset
                    dst_ds = create_mem(size_x, size_y,
                                        src_ds.RasterCount,
                                        src_ds.GetRasterBand(1).DataType)

                    # reproject the image
                    dst_ds.SetProjection(dst_sr.ExportToWkt())
                    dst_ds.SetGeoTransform(geotransform)

                    rt.reproject_image(src_ds, "", dst_ds, "", **rt_prm )

                    copy_metadata(src_ds, dst_ds)

                    # retrieve the footprint from the given GCPs
                    footprint_wkt = rt.get_footprint_wkt(src_ds, **rt_prm )

                except RuntimeError, e:
                    logger.debug("Failed using order '%i'. Error was '%s'."
                                 % (order, str(e)))
                    # the given method was not applicable, use the next one
                    continue

                else:
                    logger.debug("Successfully used order '%i'" % order)
                    # the transform method was successful, exit the loop
                    break
        else:
            # no method worked, so raise an error
            raise GCPTransformException("Could not find a valid transform method.")

        # reproject the footprint to a lon/lat projection if necessary
        if not gcp_sr.IsGeographic():
            out_sr = osr.SpatialReference()
            out_sr.ImportFromEPSG(4326)
            geom = ogr.CreateGeometryFromWkt(footprint_wkt, gcp_sr)
            geom.TransformTo(out_sr)
            footprint_wkt = geom.ExportToWkt()

        logger.debug("Calculated footprint: '%s'." % footprint_wkt)

        return dst_ds, footprint_wkt

