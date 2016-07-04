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
from os import remove, makedirs, rmdir
from os.path import (
    exists, dirname, join, isdir, samefile, commonprefix, abspath, relpath
)
import shutil
from numpy import arange
import logging
import traceback
from datetime import datetime
import string
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.template.loader import render_to_string
from eoxserver.core.system import System
from eoxserver.processing.preprocessing import WMSPreProcessor, RGB, RGBA, ORIG_BANDS
from eoxserver.processing.preprocessing.format import get_format_selection
from eoxserver.processing.preprocessing.georeference import Extent, GCPList
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
    IngestBrowseFailureResult
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
                                           seed_areas, config=config)

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
                  success_dir, failure_dir, seed_areas, config=None):
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
    except: pass

    # get the input and output filenames
    storage_path = get_storage_path()
    input_filename = abspath(get_storage_path(parsed_browse.file_name, config=config))

    # check that the input filename is valid -> somewhere under the storage dir
    if commonprefix((input_filename, storage_path)) != storage_path:
        raise IngestionException("Input path '%s' points to an invalid "
                                 "location." % parsed_browse.file_name)
    try:
        models.FileNameValidator(input_filename)
    except ValidationError, e:
        raise IngestionException("%s" % str(e), "ValidationError")

    # Get filename to store preprocessed image
    output_filename = "%s_%s" % (uuid.uuid4().hex, parsed_browse.file_name)
    output_filename = _valid_path(get_optimized_path(output_filename,
                                                     browse_layer.id + "/" + str(parsed_browse.start_time.year),
                                                     config=config))
    output_filename = preprocessor.generate_filename(output_filename)

    try:
        ingest_config = get_ingest_config(config)

        # check if a browse already exists and delete it in order to replace it
        existing_browse_model = get_existing_browse(parsed_browse.browse_identifier, coverage_id, browse_layer.id)

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
            # A browse with that identifier does not exist, so just create a new one
            logger.info("Creating new browse.")

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
                if parsed_browse.geo_type == "regularGridBrowse" and \
                        ingest_config["regular_grid_clipping"]:
                        #TODO: get clipping
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
        # move the file to success folder, or delete it right away
        delete_on_success = True
        try: delete_on_success = config.getboolean("control.ingest", "delete_on_success")
        except: pass

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
            coord_lists = [
                _unwrap_coord_list(coord_list, CRS_BOUNDS[srid])
                for coord_list in coord_lists
            ]

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
    dateline.
    """

    half = float(bounds[2])
    for (x1, _), (x2, _) in pairwise_iterative(coord_list):
        if abs(x1 - x2) > half:
            return True

    return False


def _unwrap_coord_list(coord_list, bounds):
    """ 'Unwraps' a coordinate list that crosses the dateline. """

    full = float(abs(bounds[0]) + abs(bounds[2]))
    # TODO: improve this. Might be wrong for really "long" coordinate lists that
    # start/stop in the normalized negative
    return map(lambda c: (c[0] + full if c[0] < 0 else c[0], c[1]),
               coord_list)
