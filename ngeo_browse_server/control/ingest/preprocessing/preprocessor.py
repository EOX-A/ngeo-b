#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


class NGEOPreProcessor(WMSPreProcessor):

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
            ds, footprint_wkt = geo_reference.apply(ds)

        # apply optimizations
        for optimization in self.get_optimizations(ds):
            logger.debug("Applying optimization '%s'."
                         % type(optimization).__name__)

            try:
                new_ds = optimization(ds)

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
            tmp_footprint = GEOSGeometry(footprint_wkt)
            if not tmp_bbox.contains(tmp_footprint):
                footprint_wkt = tmp_footprint.intersection(tmp_bbox).wkt

        if self.footprint_alpha:
            logger.debug("Applying optimization 'AlphaBandOptimization'.")
            opt = AlphaBandOptimization()
            opt(ds, footprint_wkt)

        output_filename = self.generate_filename(output_filename)

        if merge_with is not None:
            if original_footprint is None:
                raise ValueError(
                    "Original footprint with to be merged image required."
                )

            original_ds = gdal.Open(merge_with, gdal.GA_Update)
            merger = GDALDatasetMerger([
                GDALGeometryMaskMergeSource(original_ds, original_footprint),
                GDALGeometryMaskMergeSource(ds, footprint_wkt)
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
            logger.debug("Writing file to disc using options: %s."
                         % ", ".join(self.format_selection.creation_options))

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

        # close the dataset and write it to the disc
        final_ds = None
        final_ds = gdal.Open(output_filename, gdal.GA_Update)

        for optimization in self.get_post_optimizations(final_ds):
            logger.debug("Applying post-optimization '%s'."
                         % type(optimization).__name__)
            optimization(final_ds)

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

        num_bands = final_ds.RasterCount

        # finally close the dataset and write it to the disc
        final_ds = None

        return PreProcessResult(output_filename, footprint, num_bands)


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
