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

from itertools import izip


import numpy as np
from django.contrib.gis.geos import GEOSGeometry
from eoxserver.contrib import gdal, ogr, osr, gdal_array
from eoxserver.processing.preprocessing.util import create_mem, copy_projection


################################################################################
################################################################################
################################################################################


class Rect(tuple):
    """ Named tuple to describe areas in a 2D array like in images. The tuple
        is always in the form (offset_x, offset_y, size_x, size_y).
    """
    __slots__ = ()

    def __new__(cls, offset_x=0, offset_y=0, size_x=None, size_y=None, 
                upper_x=0, upper_y=0):

        # To subclass tuples, it is necessary to overwrite the `__new__`
        # method.

        size_x = size_x if size_x is not None else max(0, upper_x - offset_x)
        size_y = size_y if size_y is not None else max(0, upper_y - offset_y)

        return tuple.__new__(cls, (offset_x, offset_y, size_x, size_y))

    offset_x = property(lambda self: self[0])
    offset_y = property(lambda self: self[1])
    offset = property(lambda self: (self.offset_x, self.offset_y))

    size_x = property(lambda self: self[2])
    size_y = property(lambda self: self[3])
    size = property(lambda self: (self.size_x, self.size_y))

    upper_x = property(lambda self: self.offset_x + self.size_x)
    upper_y = property(lambda self: self.offset_y + self.size_y)
    upper = property(lambda self: (self.upper_x, self.upper_y))

    area = property(lambda self: self.size_x * self.size_y)


    def combination(self, other):
        """ Returns a combined rect 
        """
        return Rect(
            offset_x=min(self.offset_x, other[0]), 
            offset_y=min(self.offset_y, other[1]),
            upper_x=max(self.upper_x, other[0] + other[2]), 
            upper_y=max(self.upper_y, other[1] + other[3])
        )

    __or__ = combination

    def intersection(self, other):
        return Rect(
            offset_x=max(self.offset_x, other[0]), 
            offset_y=max(self.offset_y, other[1]),
            upper_x=min(self.upper_x, other[0] + other[2]), 
            upper_y=min(self.upper_y, other[1] + other[3])
        )

    __and__ = intersection

    def intersects(self, other):
        return self.intersection(other).area > 0


    def translated(self, (diff_x, diff_y)):
        return Rect(
            self.size_x, self.size_y, 
            self.offset_x + diff_x, self.offset_y + diff_y
        )

    __add__ = translated

    __sub__ = (lambda self, (x, y): self.translated((-x, -y)))


class BBox(tuple):
    __slots__ = ()

    def __new__(cls, minx, miny, maxx, maxy):
        # To subclass tuples, it is necessary to overwrite the `__new__`
        # method.
        if minx >= maxx or miny >= maxy:
            raise ValueError()

        return tuple.__new__(cls, (minx, miny, maxx, maxy))

    minx = property(lambda self: self[0])
    miny = property(lambda self: self[0])
    maxx = property(lambda self: self[0])
    maxy = property(lambda self: self[0])

    def combination(self, other):
        return BBox(
            min(self[0], other[0]),
            min(self[1], other[1]),
            max(self[2], other[2]),
            max(self[3], other[3])
        )

    __or__ = combination

    def intersection(self, other):
        try:
            return BBox(
                max(self[0], other[0]),
                max(self[1], other[1]),
                min(self[2], other[2]),
                min(self[3], other[3])
            )
        except ValueError:
            raise ValueError("No Intersection found")

    __and__ = intersection



class GDALDatasetWrapper(object):
    """ A utility wrapper for GDAL datasets. Eases reading of data and allows
        some convenience calculations for 
    """

    def __len__(self):
        return self.dataset.RasterCount

    @property
    def size(self):
        return self.dataset.RasterXSize, self.dataset.RasterYSize

    @property
    def resolution(self):
        gt = self.dataset.GetGeoTransform()
        return abs(gt[1]), abs(gt[5])

    @property
    def bbox(self):
        gt = self.dataset.GetGeoTransform()
        size_x, size_y = self.size
        x1 = gt[0]
        x2 = gt[0] + size_x * gt[1]
        y1 = gt[3]
        y2 = gt[3] + size_y * gt[5]

        return BBox(
            min(x1, x2), min(y1, y2),
            max(x1, x2), max(y1, y2)
        )

    @property
    def srs(self):
        srs = ogr.SpatialReference()
        srs.SetFromUserInput(self.dataset.GetProjection())
        return srs

    def read_data(self, index, rect, size_x=None, size_y=None):
        band = self.dataset.GetRasterBand(index)
        if band is None:
            raise IndexError()
        return band.ReadAsArray(*rect, buf_xsize=size_x, buf_ysize=size_y)

    def get_window(self, bbox):
        gt = self.dataset.GetGeoTransform()

        # compute target window in pixel coordinates.
        offset_x = int((bbox[0] - gt[0]) / gt[1] + 0.1)
        offset_y = int((bbox[3] - gt[3]) / gt[5] + 0.1)
        size_x = int((bbox[2] - gt[0]) / gt[1] + 0.5) - offset_x
        size_y = int((bbox[1] - gt[3]) / gt[5] + 0.5) - offset_y

        if size_x < 1 or size_y < 1:
            raise ValueError("Computed window is smaller than 1 pixel.")

        return Rect(offset_x, offset_y, size_x, size_y)



class GDALMergeSource(GDALDatasetWrapper):
    def __init__(self, dataset, use_nodata=True):
        if isinstance(dataset, basestring):
            dataset = gdal.Open(dataset)
        self.dataset = dataset
        self.use_nodata = use_nodata

    def get_mask(self, rect, size_x, size_y, source_array):
        nodata_value = src_band.GetNoDataValue()
        if self.use_nodata and not nodata_value is None:
            return np.equal(source_array, nodata_value)
        return None

    def apply_mask(self, source_array, mask_array, target_array):
        if mask_array is None:
            return source_array
        return np.choose(mask_array, (source_array, target_array))


class GDALGeometryMaskMergeSource(GDALMergeSource):
    def __init__(self, dataset, wkt, srid=None):
        super(GDALGeometryMaskMergeSource, self).__init__(dataset)

        srs = None
        srid = 4326
        if srid is not None:
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(srid)

        # create a geometry from the given WKT
        #geom = ogr.CreateGeometryFromWkt(wkt)

        # create an in-memory datasource and add one single layer
        ogr_mem_driver = ogr.GetDriverByName("Memory")
        data_source = ogr_mem_driver.CreateDataSource("xxx")
        
        layer = data_source.CreateLayer("poly", srs)

        # create a single feature and add the given geometry
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometryDirectly(ogr.Geometry(wkt=str(wkt)))
        #feature.SetField("id", 0)
        layer.CreateFeature(feature)

        # create an in-memory raster dataset with the exact same size as the 
        # dataset to be masked
        gdal_mem_driver = gdal.GetDriverByName("MEM")
        self.mask_dataset = gdal_mem_driver.Create(
            "", self.dataset.RasterXSize, self.dataset.RasterYSize, 1
        )
        band = self.mask_dataset.GetRasterBand(1)
        band.Fill(1)

        self.mask_dataset.SetGeoTransform(self.dataset.GetGeoTransform())
        self.mask_dataset.SetProjection(self.dataset.GetProjection())

        # finally rasterize the vector layer to the mask dataset
        gdal.RasterizeLayer(self.mask_dataset, (1,), layer, burn_values=(0,))

    def get_mask(self, rect, size_x, size_y, source_array):
        # read the values from the previously created mask dataset
        band = self.mask_dataset.GetRasterBand(1)
        return band.ReadAsArray(*rect, buf_xsize=size_x, buf_ysize=size_y)


class GDALAlphaMaskMergeSource(GDALMergeSource):

    def __init__(self, dataset, alpha_band_index=4):
        super(GDALAlphaMaskMergeSource, self).__init__(dataset)
        
        if alpha_band_index > self.dataset.RasterCount or alpha_band_index < 0:
            raise ValueError("Invalid band index for alpha band.")

        self.alpha_band_index = alpha_band_index


    def get_mask(self, rect, size_x, size_y, source_array):
        alpha_band = self.dataset.GetRasterBand(self.alpha_band_index)
        dt = gdal_array.GDALTypeCodeToNumericTypeCode(alpha_band.DataType)
        
        raw_alphas = alpha_band.ReadAsArray(
            *rect, buf_xsize=size_x, buf_ysize=size_y
        )
        if issubclass(dt, np.floating):
            return raw_alphas
        elif issubclass(dt, np.integer):
            return raw_alphas.astype(np.float32, copy=False) / np.iinfo(dt).max
        else:
            raise Exception("Could not convert alpha mask.")


    def apply_mask(self, source_array, mask_array, target_array):
        dt = target_array.dtype
        return dt(
            mask_array * source_array + (1 - mask_array) * target_array, 
            copy=False
        )


class GDALMergeTarget(GDALDatasetWrapper):
    def __init__(self, filename, size_x, size_y, geotransform, band_num, 
                 data_type, projection, driver=None, creation_options=None):
        driver = gdal.GetDriverByName(driver or "GTiff")
        self.dataset = driver.Create(
            filename, size_x, size_y, band_num, data_type, creation_options or []
        )
        self.dataset.SetGeoTransform(geotransform)
        self.dataset.SetProjection(projection)

    @classmethod
    def from_sources(cls, filename, sources, driver=None, creation_options=None):
        # use smallest resolution
        first = sources[0]
        others = sources[1:]

        res_x, res_y = first.resolution
        bbox = first.bbox
        first_srs = osr.SpatialReference()
        first_srs.ImportFromWkt(first.dataset.GetProjection())
        bandnum = len(first)

        for source in others:
            # check the sources
            source_srs = osr.SpatialReference()
            source_srs.ImportFromWkt(source.dataset.GetProjection())
            if not source_srs.IsSame(first_srs) or len(source) != len(first):
                raise Exception("Could not create merge target.")

            new_res_x, new_res_y = source.resolution
            bbox = bbox | source.bbox

            res_x = min(res_x, new_res_x)
            res_y = min(res_y, new_res_y)

        # create output dataset
        size_x = int((bbox[2] - bbox[0]) / res_x + .5)
        size_y = int((bbox[3] - bbox[1]) / res_y + .5)
        gt = bbox[0], res_x, 0.0, bbox[3], 0.0, -res_y

        return cls(
            filename, size_x, size_y, gt, first.dataset.RasterCount,
            first.dataset.GetRasterBand(1).DataType,
            first.dataset.GetProjection(), driver, creation_options
        )


    def write_data(self, index, rect, data):
        band = self.dataset.GetRasterBand(index)
        if band is None:
            raise IndexError()

        return band.WriteArray(data, *rect.offset)


class GDALDatasetMerger(object):
    def __init__(self, sources=None, target=None):
        self.sources = sources or []
        self.target = target

    def add_source(self, source):
        self.sources.append(source)

    def merge(self, out_filename=None, out_driver=None, creation_options=None):
        if not self.sources:
            raise ValueError("No sources applied")
        target = self.target or GDALMergeTarget.from_sources(
            out_filename, self.sources, out_driver, creation_options
        )

        whole_bbox = target.bbox

        for source in self.sources:
            for band_index in xrange(1, len(target) + 1):
                target_bbox = whole_bbox & source.bbox

                # compute pixel windows
                source_rect = source.get_window(target_bbox)
                target_rect = target.get_window(target_bbox)

                # read the source array with the given window
                source_data = source.read_data(
                    band_index, source_rect, *target_rect.size
                )

                # get a mask if available
                mask_data = source.get_mask(
                    source_rect, target_rect.size_x, target_rect.size_y, 
                    source_data
                )
                if mask_data is not None:
                    # first read the data from the target, to allow applying a 
                    # mask
                    target_data = target.read_data(
                        band_index, target_rect, *target_rect.size
                    )

                    masked = source.apply_mask(
                        source_data, mask_data, target_data
                    )
                    # hack? seems to be necessary
                    source_data = masked

                target.write_data(band_index, target_rect, source_data)

        return target.dataset

    __call__ = merge

################################################################################
################################################################################
################################################################################

def generate_footprint_wkt(ds, simplification_factor=2):
    """ Generate a fooptrint from a raster, using black/no-data as exclusion
    """
    
    # create an empty boolean array initialized as 'False' to store where
    # values exist as a mask array.
    nodata_map = np.zeros((ds.RasterYSize, ds.RasterXSize),
                             dtype=np.bool)
    
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
    tmp_band.WriteArray(nodata_map.astype(np.uint8))
    
    # create an OGR in memory layer to hold the created polygon
    sr = osr.SpatialReference(); sr.ImportFromWkt(ds.GetProjectionRef())
    ogr_ds = ogr.GetDriverByName('Memory').CreateDataSource('out')
    layer = ogr_ds.CreateLayer('poly', sr.sr, ogr.wkbPolygon)
    fd = ogr.FieldDefn('DN', ogr.OFTInteger)
    layer.CreateField(fd)
    
    # polygonize the mask band and store the result in the OGR layer
    gdal.Polygonize(tmp_band, tmp_band, layer, 0)
    
    if layer.GetFeatureCount() != 1:
        # if there is more than one polygon, compute the minimum bounding polygon
        geometry = ogr.Geometry(ogr.wkbPolygon)
        while True:
            feature = layer.GetNextFeature()
            if not feature: break
            geometry = geometry.Union(feature.GetGeometryRef())
        
        # TODO: improve this for a better minimum bounding polygon
        geometry = geometry.ConvexHull()
    
    else:
        # obtain geometry from the first (and only) layer
        feature = layer.GetNextFeature()
        geometry = feature.GetGeometryRef()
    
    if geometry.GetGeometryType() not in (ogr.wkbPolygon, ogr.wkbMultiPolygon):
        raise RuntimeError("Error during poligonization. Wrong geometry "
                           "type.")
    
    # check if reprojection to latlon is necessary
    if not sr.IsGeographic():
        dst_sr = osr.SpatialReference(); dst_sr.ImportFromEPSG(4326)
        try:
            geometry.TransformTo(dst_sr.sr)
        except RuntimeError:
            geometry.Transform(osr.CoordinateTransformation(sr.sr, dst_sr.sr))
    
    gt = ds.GetGeoTransform()
    resolution = min(abs(gt[1]), abs(gt[5]))

    simplification_value = simplification_factor * resolution
    
    # simplify the polygon. the tolerance value is *really* vague
    try:
        # SimplifyPreserveTopology() available since OGR 1.9.0
        geometry = geometry.SimplifyPreserveTopology(simplification_value)
    except AttributeError:
        # use GeoDjango bindings if OGR is too old
        geometry = ogr.CreateGeometryFromWkt(
            GEOSGeometry(
                geometry.ExportToWkt()
            ).simplify(simplification_value, True).wkt
        )
    
    return geometry.ExportToWkt()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise ValueError("Too few arguments given. Usage: inputA inputB (inputC ...) output")


    inputs = sys.argv[1:-1]
    out_filename = sys.argv[-1]


    merger = GDALDatasetMerger([
        GDALGeometryMaskMergeSource(ds, generate_footprint_wkt(ds))
        for ds in map(gdal.Open, inputs)
    ])

    merger.merge(out_filename)
