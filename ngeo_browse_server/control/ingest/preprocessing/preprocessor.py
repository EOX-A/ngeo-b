#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 European Space Agency
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
from uuid import uuid4
import tempfile
from os.path import join
from os import (remove, rename)

from django.contrib.gis.geos import (
    GEOSGeometry, MultiPolygon, Polygon, LinearRing,
)
from eoxserver.contrib import gdal, osr, ogr
from eoxserver.processing.preprocessing import (
    WMSPreProcessor, PreProcessResult
)
from eoxserver.processing.preprocessing.optimization import *
from eoxserver.processing.preprocessing.util import (
    create_mem_copy, create_mem, copy_metadata, cleanup_temp
)
from eoxserver.processing.gdal import reftools
from eoxserver.processing.preprocessing.exceptions import GCPTransformException
from eoxserver.resources.coverages.geo import getExtentFromRectifiedDS

from ngeo_browse_server.control.ingest.preprocessing.merge import (
    GDALDatasetMerger, GDALGeometryMaskMergeSource
)


logger = logging.getLogger(__name__)


# enum for bandmode
RGB = range(3)


class NGEOPreProcessor(WMSPreProcessor):

    def __init__(self, format_selection, overviews=True, overviews_self=False,
                 crs=None, bands=None, bandmode=RGB, footprint_alpha=False,
                 color_index=False, palette_file=None, no_data_value=None,
                 overview_resampling=None, overview_levels=None,
                 overview_minsize=None, radiometric_interval_min=None,
                 radiometric_interval_max=None, sieve_max_threshold=None,
                 simplification_factor=None, temporary_directory=None):

        self.format_selection = format_selection
        self.overviews_self = overviews_self  # Don't use EOxServer one
        if overviews_self:
            self.overviews = False
        else:
            self.overviews = overviews
        self.overview_resampling = overview_resampling
        self.overview_levels = overview_levels
        self.overview_minsize = overview_minsize

        self.crs = crs

        self.bands = bands
        self.bandmode = bandmode
        self.footprint_alpha = footprint_alpha
        self.color_index = color_index
        self.palette_file = palette_file
        self.no_data_value = no_data_value
        self.radiometric_interval_min = radiometric_interval_min
        self.radiometric_interval_max = radiometric_interval_max

        if sieve_max_threshold is not None:
            self.sieve_max_threshold = sieve_max_threshold
        else:
            self.sieve_max_threshold = 0

        if simplification_factor is not None:
            self.simplification_factor = simplification_factor
        else:
            # default 2 * resolution == 2 pixels
            self.simplification_factor = 2

        self.temporary_directory = temporary_directory

    def process(self, input_filename, output_filename,
                geo_reference=None, generate_metadata=True,
                merge_with=None, original_footprint=None):

        # open the dataset and create an In-Memory Dataset as copy
        # to perform optimizations
        ds = create_mem_copy(gdal.Open(input_filename))

        gt = ds.GetGeoTransform()
        footprint_wkt = None

        if not geo_reference:
            if gt == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
                if ds.GetGCPCount() > 0:
                    geo_reference = InternalGCPs()
                else:
                    raise ValueError("No geospatial reference for "
                                     "unreferenced dataset given.")

        if geo_reference:
            logger.debug("Applying geo reference '%s'."
                         % type(geo_reference).__name__)
            # footprint is always in EPSG:4326
            ds, footprint_wkt = geo_reference.apply(ds)

        # apply optimizations
        for optimization in self.get_optimizations(ds):
            logger.debug("Applying optimization '%s'."
                         % type(optimization).__name__)

            try:
                new_ds = optimization(ds)
                new_ds.FlushCache()

                if new_ds is not ds:
                    # cleanup afterwards
                    cleanup_temp(ds)
                    ds = new_ds
            except:
                cleanup_temp(ds)
                raise


        # generate the footprint from the dataset
        if not footprint_wkt:
            logger.debug("Generating footprint.")
            footprint_wkt = self._generate_footprint_wkt(ds)
        # check that footprint is inside of extent of generated image
        # regenerate otherwise
        else:
            tmp_extent = getExtentFromRectifiedDS(ds)
            tmp_bbox = Polygon.from_bbox((tmp_extent[0], tmp_extent[1],
                                          tmp_extent[2], tmp_extent[3]))
            # transform image bbox to EPSG:4326 if necessary
            proj = ds.GetProjection()
            srs = osr.SpatialReference()
            try:
                srs.ImportFromWkt(proj)
                srs.AutoIdentifyEPSG()
                ptype = "PROJCS" if srs.IsProjected() else "GEOGCS"
                srid = int(srs.GetAuthorityCode(ptype))
                if srid != '4326':
                    out_srs = osr.SpatialReference()
                    out_srs.ImportFromEPSG(4326)
                    transform = osr.CoordinateTransformation(srs, out_srs)
                    tmp_bbox2 = ogr.CreateGeometryFromWkt(tmp_bbox.wkt)
                    tmp_bbox2.Transform(transform)
                    tmp_bbox = GEOSGeometry(tmp_bbox2.ExportToWkt())
            except (RuntimeError, TypeError), e:
                logger.warn("Projection: %s" % proj)
                logger.warn("Failed to identify projection's EPSG code."
                    "%s: %s" % ( type(e).__name__ , str(e) ) )

            tmp_footprint = GEOSGeometry(footprint_wkt)
            if not tmp_bbox.contains(tmp_footprint):
                logger.debug("Re-generating footprint because not inside of "
                             "generated image.")
                footprint_wkt = tmp_footprint.intersection(tmp_bbox).wkt

        if self.footprint_alpha:
            logger.debug("Applying optimization 'AlphaBandOptimization'.")
            opt = AlphaBandOptimization()
            opt(ds, footprint_wkt)
            ds.FlushCache()

        output_filename = self.generate_filename(output_filename)

        if merge_with is not None:
            if original_footprint is None:
                raise ValueError(
                    "Original footprint with to be merged image required."
                )

            original_ds = gdal.Open(merge_with, gdal.GA_Update)
            merger = GDALDatasetMerger([
                GDALGeometryMaskMergeSource(
                    original_ds, original_footprint,
                    temporary_directory=self.temporary_directory
                ),
                GDALGeometryMaskMergeSource(
                    ds, footprint_wkt,
                    temporary_directory=self.temporary_directory
                )
            ])

            final_ds = merger.merge(
                output_filename, self.format_selection.driver_name,
                self.format_selection.creation_options
            )

            # cleanup previous file
            driver = original_ds.GetDriver()
            original_ds = None
            driver.Delete(merge_with)

            cleanup_temp(ds)

        else:
            logger.debug(
                "Writing single file '%s' using options: %s."
                % (
                    output_filename,
                    ", ".join(self.format_selection.creation_options)
                )
            )
            logger.debug("Metadata tags to be written: %s"
                         % ", ".join(ds.GetMetadata_List("") or []))

            # save the file to the disc
            driver = gdal.GetDriverByName(self.format_selection.driver_name)
            final_ds = driver.CreateCopy(
                output_filename, ds,
                options=self.format_selection.creation_options
            )

            # cleanup
            cleanup_temp(ds)

        for optimization in self.get_post_optimizations(final_ds):
            logger.debug("Applying post-optimization '%s'."
                         % type(optimization).__name__)
            optimization(final_ds)

        num_bands = final_ds.RasterCount

        if self.overviews_self:
            logger.debug("Applying OverviewOptimization ourselves")
            levels = self.overview_levels

            # calculate the overviews automatically.
            if not levels:
                desired_size = abs(self.overview_minsize or 256)
                size = max(final_ds.RasterXSize, final_ds.RasterYSize)
                level = 1
                levels = []

                while size > desired_size:
                    size /= 2
                    level *= 2
                    levels.append(level)

            logger.debug(
                "Building overview levels %s with resampling method '%s'."
                % (", ".join(map(str, levels)), self.overview_resampling)
            )

            final_ds.FlushCache()
            filename = final_ds.GetFileList()[0]
            final_filename = filename
            driver = final_ds.GetDriver()

            # finally close the dataset and write it to the disc
            final_ds = None

            # re-build overviews
            # use .ovr trick to accommodate very large images (>65536 pixels)
            for level in levels:
                try:
                    input_ds = gdal.Open(filename, gdal.GA_ReadOnly)
                    input_ds.BuildOverviews(self.overview_resampling, [2])
                    filename = '%s.ovr' % filename
                    input_ds = None
                except RuntimeError:
                    logger.warning(
                        "Overview building failed for level '%s'." % level
                    )

            tmp_filename = join(tempfile.gettempdir(), '%s.tif' % uuid4().hex)
            tmp_ds = driver.CreateCopy(
                tmp_filename,
                gdal.Open(final_filename, gdal.GA_ReadOnly),
                options=self.format_selection.creation_options + [
                    "COPY_SRC_OVERVIEWS=YES",
                ]
            )
            tmp_ds = None
            filename = final_filename
            for level in levels:
                filename = '%s.ovr' % filename
                remove(filename)
            rename(tmp_filename, final_filename)

        else:
            # finally close the dataset and write it to the disc
            final_ds = None

        # generate metadata if requested
        footprint = None
        if generate_metadata:
            normalized_space = Polygon.from_bbox((-180, -90, 180, 90))
            non_normalized_space = Polygon.from_bbox((180, -90, 360, 90))

            footprint = GEOSGeometry(footprint_wkt)

            outer = non_normalized_space.intersection(footprint)

            if len(outer):
                footprint = MultiPolygon(
                    *map(lambda p:
                        Polygon(*map(lambda ls:
                            LinearRing(*map(lambda point:
                                (point[0] - 360, point[1]), ls.coords
                            )), tuple(p)
                        )), (outer,)
                    )
                ).union(normalized_space.intersection(footprint))
            else:
                if isinstance(footprint, Polygon):
                    footprint = MultiPolygon(footprint)

            if original_footprint:
                logger.debug("Merging footprint.")
                footprint = footprint.union(GEOSGeometry(original_footprint))

            logger.debug("Calculated Footprint: '%s'" % footprint.wkt)

        return PreProcessResult(output_filename, footprint, num_bands)

    def _generate_footprint_wkt(self, ds):
        """ Generate a footprint from a raster, using black/no-data as
            exclusion
        """

        # create an empty boolean array initialized as 'False' to store where
        # values exist as a mask array.
        nodata_map = numpy.zeros((ds.RasterYSize, ds.RasterXSize),
                                 dtype=numpy.bool)

        for idx in range(1, ds.RasterCount + 1):
            band = ds.GetRasterBand(idx)
            raster_data = band.ReadAsArray()
            nodata = band.GetNoDataValue()

            if nodata is None:
                nodata = 0

            # apply the output to the map
            nodata_map |= (raster_data != nodata)

        # create a temporary in-memory dataset and write the nodata mask
        # into its single band
        tmp_ds = create_mem(ds.RasterXSize + 2, ds.RasterYSize + 2, 1,
                            gdal.GDT_Byte)
        copy_projection(ds, tmp_ds)
        tmp_band = tmp_ds.GetRasterBand(1)
        tmp_band.WriteArray(nodata_map.astype(numpy.uint8))

        # Remove unwanted small areas of nodata
        # www.gdal.org/gdal__alg_8h.html#a33309c0a316b223bd33ae5753cc7f616
        no_pixels = tmp_ds.RasterXSize * tmp_ds.RasterYSize
        threshold = 4
        max_threshold = (no_pixels / 16)
        if self.sieve_max_threshold > 0:
            max_threshold = self.sieve_max_threshold
        while threshold <= max_threshold and threshold < 2147483647:
            gdal.SieveFilter(tmp_band, None, tmp_band, threshold, 4)
            threshold *= 4

        #for debugging:
        #gdal.GetDriverByName('GTiff').CreateCopy('/tmp/test.tif', tmp_ds)

        # create an OGR in memory layer to hold the created polygon
        sr = osr.SpatialReference()
        sr.ImportFromWkt(ds.GetProjectionRef())
        ogr_ds = ogr.GetDriverByName('Memory').CreateDataSource('out')
        layer = ogr_ds.CreateLayer('poly', sr, ogr.wkbPolygon)
        fd = ogr.FieldDefn('DN', ogr.OFTInteger)
        layer.CreateField(fd)

        # polygonize the mask band and store the result in the OGR layer
        gdal.Polygonize(tmp_band, tmp_band, layer, 0)

        tmp_ds = None

        if layer.GetFeatureCount() > 1:
            # if there is more than one polygon, compute the minimum
            # bounding polygon
            logger.debug("Merging %s features in footprint."
                         % layer.GetFeatureCount())

            # union all features in one multi-polygon
            geometry = ogr.Geometry(ogr.wkbMultiPolygon)
            while True:
                feature = layer.GetNextFeature()
                if not feature:
                    break
                geometry.AddGeometry(feature.GetGeometryRef())
            geometry = geometry.UnionCascaded()

            # TODO: improve this for a better minimum bounding polygon
            geometry = geometry.ConvexHull()

        elif layer.GetFeatureCount() < 1:
            # there was an error during polygonization
            raise RuntimeError("Error during polygonization. No feature "
                               "obtained.")
        else:
            # obtain geometry from the first (and only) layer
            feature = layer.GetNextFeature()
            geometry = feature.GetGeometryRef()

        if geometry.GetGeometryType() != ogr.wkbPolygon:
            raise RuntimeError("Error during polygonization. Wrong geometry "
                               "type: %s" % ogr.GeometryTypeToName(
                                   geometry.GetGeometryType()))

        # check if reprojection to latlon is necessary
        if not sr.IsGeographic():
            dst_sr = osr.SpatialReference()
            dst_sr.ImportFromEPSG(4326)
            try:
                geometry.TransformTo(dst_sr)
            except RuntimeError:
                geometry.Transform(osr.CoordinateTransformation(sr, dst_sr))

        gt = ds.GetGeoTransform()
        resolution = min(abs(gt[1]), abs(gt[5]))

        simplification_value = self.simplification_factor * resolution

        #for debugging:
        #geometry.GetGeometryRef(0).GetPointCount()

        # simplify the polygon. the tolerance value is *really* vague
        try:
            # SimplifyPreserveTopology() available since OGR 1.9.0
            geometry = geometry.SimplifyPreserveTopology(simplification_value)
        except AttributeError:
            # use GeoDjango bindings if OGR is too old
            geometry = ogr.CreateGeometryFromWkt(
                GEOSGeometry(geometry.ExportToWkt()).simplify(
                    simplification_value, True
                ).wkt
            )

        return geometry.ExportToWkt()


class InternalGCPs(object):
    def __init__(self, srid=4326):
        self.srid = srid

    def apply(self, src_ds):
        # setup
        dst_sr = osr.SpatialReference()
        dst_sr.ImportFromEPSG(self.srid)

        logger.debug("Using internal GCP Projection.")
        num_gcps = src_ds.GetGCPCount()

        # Try to find and use the best transform method/order.
        # Orders are: -1 (TPS), 3, 2, and 1 (all GCP)
        # Loop over the min and max GCP number to order map.
        for min_gcpnum, max_gcpnum, order in [(3, None, -1), (10, None, 3), (6, None, 2), (3, None, 1)]:
            # if the number of GCP matches
            if num_gcps >= min_gcpnum and (max_gcpnum is None or num_gcps <= max_gcpnum):
                try:

                    if (order < 0):
                        # let the reftools suggest the right interpolator
                        rt_prm = reftools.suggest_transformer(src_ds)
                    else:
                        # use the polynomial GCP interpolation as requested
                        rt_prm = {
                            "method": reftools.METHOD_GCP, "order": order
                        }

                    logger.debug("Trying order '%i' {method:%s,order:%s}" % (
                        order, reftools.METHOD2STR[rt_prm["method"]],
                        rt_prm["order"]
                    ))

                    # get the suggested pixel size/geotransform
                    size_x, size_y, gt = reftools.suggested_warp_output(
                        src_ds,
                        None,
                        dst_sr.ExportToWkt(),
                        **rt_prm
                    )
                    if size_x > 100000 or size_y > 100000:
                        raise RuntimeError("Calculated size exceeds limit.")
                    logger.debug("New size is '%i x %i'" % (size_x, size_y))

                    # create the output dataset
                    dst_ds = create_mem(size_x, size_y,
                                        src_ds.RasterCount,
                                        src_ds.GetRasterBand(1).DataType)

                    # reproject the image
                    dst_ds.SetProjection(dst_sr.ExportToWkt())
                    dst_ds.SetGeoTransform(gt)

                    reftools.reproject_image(src_ds, "", dst_ds, "", **rt_prm)

                    copy_metadata(src_ds, dst_ds)

                    # retrieve the footprint from the given GCPs
                    footprint_wkt = reftools.get_footprint_wkt(src_ds, **rt_prm)

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
            raise GCPTransformException(
                "Could not find a valid transform method."
            )

        # reproject the footprint to a lon/lat projection if necessary
        if not dst_sr.IsGeographic():
            out_sr = osr.SpatialReference()
            out_sr.ImportFromEPSG(4326)
            geom = ogr.CreateGeometryFromWkt(footprint_wkt, gcp_sr)
            geom.TransformTo(out_sr)
            footprint_wkt = geom.ExportToWkt()

        logger.debug("Calculated footprint: '%s'." % footprint_wkt)

        return dst_ds, footprint_wkt
