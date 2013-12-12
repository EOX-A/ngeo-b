
from django.contrib.gis.geos import GEOSGeometry, Polygon
from eoxserver.contrib import gdal
from eoxserver.processing.preprocessing import WMSPreProcessor
from eoxserver.processing.preprocessing.optimization import *
from eoxserver.processing.preprocessing.util import create_mem_copy

from ngeo_browse_server.control.ingest.preprocessing.merge import (
    GDALDatasetMerger
)


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
            if gt == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0): # TODO: maybe use a better check
                raise ValueError("No geospatial reference for unreferenced "
                                 "dataset given.")
        else:
            logger.debug("Applying geo reference '%s'."
                         % type(geo_reference).__name__)
            ds, footprint_wkt = geo_reference.apply(ds)
        
        # apply optimizations
        for optimization in self.get_optimizations(ds):
            logger.debug("Applying optimization '%s'."
                         % type(optimization).__name__)
            new_ds = optimization(ds)
            ds = None
            ds = new_ds
            
        # generate the footprint from the dataset
        if not footprint_wkt:
            logger.debug("Generating footprint.")
            footprint_wkt = self._generate_footprint_wkt(ds)
        
        
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

            original_ds = gdal.Open(merge_with)
            merger = GDALDatasetMerger([
                GDALGeometryMaskMergeSource(original_ds, original_footprint),
                GDALGeometryMaskMergeSource(ds, footprint_wkt)
            ])

            ds = merger.merge(
                output_filename, self.format_selection.driver_name,
                self.format_selection.creation_options
            )

        else:
            logger.debug("Writing file to disc using options: %s."
                         % ", ".join(self.format_selection.creation_options))
            
            logger.debug("Metadata tags to be written: %s"
                         % ", ".join(ds.GetMetadata_List("") or []))
            
            # save the file to the disc
            driver = gdal.GetDriverByName(self.format_selection.driver_name)
            ds = driver.CreateCopy(output_filename, ds,
                                   options=self.format_selection.creation_options)
        
        for optimization in self.get_post_optimizations(ds):
            logger.debug("Applying post-optimization '%s'."
                         % type(optimization).__name__)
            optimization(ds)
        
        # generate metadata if requested
        footprint = None
        if generate_metadata:
            normalized_space = Polygon.from_bbox((-180, -90, 180, 90))
            non_normalized_space = Polygon.from_bbox((180, -90, 360, 90))
            
            footprint = GEOSGeometry(footprint_wkt)
            #.intersection(normalized_space)
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
                
            
            
            logger.info("Calculated Footprint: '%s'" % footprint.wkt)
            
            
            
            # use the provided footprint
            #geom = OGRGeometry(footprint_wkt)
            #exterior = []
            #for x, y in geom.exterior_ring.tuple:
            #    exterior.append(y); exterior.append(x)
            
            #polygon = [exterior]
        
        num_bands = ds.RasterCount
        
        # close the dataset and write it to the disc
        ds = None
        
        return PreProcessResult(output_filename, footprint, num_bands)
