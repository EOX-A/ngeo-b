import sys
from os import walk
from os.path import join, exists, dirname
import tempfile
import shutil
from cStringIO import StringIO
from lxml import etree
import logging

from osgeo import gdal, osr
from django.conf import settings
from django.test.client import Client
from django.core.management import execute_from_command_line
from eoxserver.core.system import System
from eoxserver.resources.coverages import models as eoxs_models
from eoxserver.resources.coverages.geo import getExtentFromRectifiedDS

from ngeo_browse_server.config import get_ngeo_config, reset_ngeo_config
from ngeo_browse_server.config import models
from ngeo_browse_server.control.ingest import safe_makedirs
from ngeo_browse_server.control.ingest.config import INGEST_SECTION
from ngeo_browse_server.mapcache import models as mapcache_models


logger = logging.getLogger(__name__)

gdal.UseExceptions()
osr.UseExceptions()


class IngestResult(object):
    """ Helper class to parse an ingest result. """
    
    def __init__(self, xml):
        def ns_bsi(tag):
            return "{http://ngeo.eo.esa.int/schema/browse/ingestion}" + tag
        
        document = etree.fromstring(xml)
        self.status = document.find(".//" + ns_bsi("status")).text
        self.to_be_replaced = int(document.find(".//" + ns_bsi("toBeReplaced")).text)
        self.actually_inserted = int(document.find(".//" + ns_bsi("actuallyInserted")).text)
        self.actually_replaced = int(document.find(".//" + ns_bsi("actuallyReplaced")).text)
        self._records = []
        for record in document.findall(".//" + ns_bsi("briefRecord")):
            identifier = record.findtext(ns_bsi("identifier"))
            status = record.findtext(ns_bsi("status"))
            exception_code, exception_message = None, None
            if status == "failure":
                exception_code = record.findtext(".//" + ns_bsi("exceptionCode"))
                exception_message = record.findtext(".//" + ns_bsi("exceptionMessage"))
            self._records.append((identifier, status, exception_code, exception_message))
    
    
    def __iter__(self):
        return iter(self._records)
    
    records = property(lambda self: self._records)
    successful = property(lambda self: [record for record in self._records if record[1] == "success"])
    failed = property(lambda self: [record for record in self._records if record[1] == "failure"])
    

class BaseTestCaseMixIn(object):
    """ Base Mixin for ngEO test cases using the http interface. Compares the 
    expected response/status code with the actual results.
    """
    
    fixtures = ["initial_rangetypes.json", "ngeo_browse_layer.json", 
                "eoxs_dataset_series.json", "ngeo_mapcache.json"]
    
    # pointing to the actual data directory. Will be copied to a temporary directory
    storage_dir = "data/reference_test_data"
    multi_db = True
    
    surveilled_model_classes = (
        models.Browse,
        eoxs_models.RectifiedDatasetRecord,
        mapcache_models.Time
    )
    
    copy_to_optimized = () # list of filenames to be copied to the optimized dir
    
    default_configuration = {
        (INGEST_SECTION, "optimized_files_postfix"): "_proc",
        (INGEST_SECTION, "compression"): "NONE",
        (INGEST_SECTION, "jpeg_quality"): "75",
        (INGEST_SECTION, "zlevel"): "6",
        (INGEST_SECTION, "tiling"): "true",
        (INGEST_SECTION, "overviews"): "true",
        (INGEST_SECTION, "overview_resampling"): "NEAREST",
        (INGEST_SECTION, "overview_levels"): None,
        (INGEST_SECTION, "overview_minsize"): "256",
        (INGEST_SECTION, "color_index"): "false",
        (INGEST_SECTION, "footprint_alpha"): "true",
        (INGEST_SECTION, "delete_on_success"): "false",
        (INGEST_SECTION, "leave_original"): "false",
        # storage_dir, success_dir, failure_dir and optimized_files_dir are set
        # automatically.
    }
    
    configuration = {}
    
    def setUp(self):
        super(BaseTestCaseMixIn, self).setUp()
        self.setUp_files()
        self.setUp_config()
        
        # check the number of DS, Browse and Time models in the database
        self.model_counts = {}
        
        # wrap the ingestion with model counter
        self.add_counts(*self.surveilled_model_classes)
        self.response = self.execute()
        self.add_counts(*self.surveilled_model_classes)
    
    
    def tearDown(self):
        super(BaseTestCaseMixIn, self).tearDown()
        self.tearDown_files()

        
    def setUp_files(self):
        # create a temporary storage directory and copy the reference test data
        # into it point the control.ingest.storage_dir to this location
        self.temp_storage_dir = tempfile.mktemp() # create a temp dir
        
        config = get_ngeo_config()
        section = "control.ingest"
        
        shutil.copytree(join(settings.PROJECT_DIR, self.storage_dir), self.temp_storage_dir)
        config.set(section, "storage_dir", self.temp_storage_dir)
        
        # create a temporary optimized files directory, empty. point the 
        # control.ingest.optimized_files_dir to it
        self.temp_optimized_files_dir = tempfile.mkdtemp()
        config.set(section, "optimized_files_dir", self.temp_optimized_files_dir)
        
        self.temp_success_dir = tempfile.mkdtemp()
        config.set(section, "success_dir", self.temp_success_dir)
        
        self.temp_failure_dir = tempfile.mkdtemp()
        config.set(section, "failure_dir", self.temp_failure_dir)
        
        # copy files to optimized dir
        for filename_src, filename_dst in self.copy_to_optimized:
            filename_src = join(settings.PROJECT_DIR, "data", filename_src)
            filename_dst = join(self.temp_optimized_files_dir, filename_dst)
            safe_makedirs(dirname(filename_dst))
            shutil.copy(filename_src, filename_dst)
        
    
    def setUp_config(self):
        # set up default config and specific config
        
        config = get_ngeo_config()
        for configuration in (self.default_configuration, self.configuration):
            for (section, option), value in configuration.items():
                if value is not None:
                    config.set(section, option, value)
                else:
                    config.remove_option(section, option)
    
    
    def tearDown_files(self):
        # remove the created temporary directories
        
        for d in (self.temp_storage_dir, self.temp_optimized_files_dir,
                  self.temp_success_dir, self.temp_failure_dir):
            shutil.rmtree(d)
        
        # reset the config settings
        reset_ngeo_config()
    
    def add_counts(self, *model_classes):
        # save the count of each model class to be checked later on.
        for model_cls in model_classes:
            self.model_counts.setdefault(model_cls.__name__, []).append(model_cls.objects.count())
    
    def get_file_list(self, path):
        # convenience function to get a list of files from a directory
        
        files = []
        for _, _, filenames in walk(path):
            files.extend(filenames)
        
        return files
    


class HttpMixIn(object):
    """ Base class for testing the HTTP interface
    """
    request = None
    request_file = None
    url = "/ingest/"
    
    expected_status = 200
    expected_response = None
    
    def get_request(self):
        if self.request:
            return self.request
        
        elif self.request_file:
            filename = join(settings.PROJECT_DIR, "data", self.request_file)
            with open(filename) as f:
                return str(f.read())
    
    
    def get_response(self):
        return self.response.content
    
    
    def execute(self, request=None, url=None):
        if not url:
            url = self.url
        
        if not request:
            request = self.get_request()
        
        client = Client()        
        return client.post(url, request, "text/xml")

    
    def test_expected_status(self):
        self.assertEqual(self.expected_status, self.response.status_code)
    
    
    def test_expected_response(self):
        if self.expected_response is None:
            self.skipTest("No expected response given.")
        
        self.assertEqual(self.expected_response, self.response.content)



class CliMixIn(object):
    command = "ngeo_ingest_browse_report"
    args = ()
    kwargs = {}
    
    def execute(self, *args):
        # construct command line parameters
        args = ["manage.py", self.command]
        if isinstance(args, (list, tuple)):
            args.extend(self.args)
        elif isinstance(args, basestring):
            args.extend(self.args.split(" "))
        
        for key, value in self.kwargs.items():
            args.append("-%s" % key if len(key) == 1 else "--%s" % key)
            if isinstance(value, (list, tuple)):
                args.extend(value)
            else: 
                args.append(value)
        
        # redirect stdio/stderr to buffer
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            # execute command
            self.execute_command(args)
            
            # retrieve string
            stdout_str = sys.stdout.getvalue()
            stderr_str = sys.stderr.getvalue()
        
        finally:
            # reset stdio/stderr
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        
        return stdout_str, stderr_str
    
    
    def execute_command(self, args):
        """ This function actually executes the given command. It raises a
        failure if the command prematurely quits.
        """
        
        try:
            execute_from_command_line(args)
        except SystemExit:
            if not self.expect_failure:
                self.fail("Command '%s' failed and exited. Message was: '%s'" % ( 
                          " ".join(args) , 
                          "".join(sys.stderr.getvalue().rsplit("\n", 1))))

    def get_response(self):
        # return either stout
        return self.response[0]
        


class IngestTestCaseMixIn(BaseTestCaseMixIn):
    """ Mixin for ngEO ingest test cases. Checks whether or not the browses with
    the specified IDs have been correctly registered.  
    """
    
    expected_ingested_browse_ids = ()
    expected_ingested_coverage_ids = None
    expected_inserted_into_series = None
    expected_optimized_files = ()
    expected_deleted_files = None
    
    expected_generated_success_browse_report = None
    
    
    def test_expected_ingested_browses(self):
        """ Check that the expected browse IDs are ingested, rectified datasets
        are created and the count is equal to the produced optimized files.
        """
        
        System.init()
        
        if not self.expected_ingested_browse_ids:
            self.skipTest("No expected browse IDs given.")
        
        browse_ids = self.expected_ingested_browse_ids
        coverage_ids = self.expected_ingested_coverage_ids or browse_ids
        
        assert(len(coverage_ids) == len(browse_ids))
        
        for browse_id, coverage_id in zip(browse_ids, coverage_ids):
            # check if the browse with either the browse ID or coverage ID exists
            if browse_id is not None:
                self.assertTrue(
                    models.Browse.objects.filter(
                        browse_identifier__value=browse_id
                    ).exists()
                )
            elif coverage_id is not None:
                self.assertTrue(
                    models.Browse.objects.filter(
                        coverage_id=coverage_id
                    ).exists()
                )
            
            # test if the EOxServer rectified dataset was created
            coverage_wrapper = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": coverage_id}
            )
            self.assertTrue(coverage_wrapper is not None)
        
        browse_report_file_mod = 0
        if len(browse_ids) > 0:
            # if at least one browse was successfully ingested, a browse report
            # must also be present.
            browse_report_file_mod = 1
        
        # test that the correct number of files was moved/created in the success
        # directory
        files = self.get_file_list(self.temp_success_dir)
        self.assertEqual(len(browse_ids) + browse_report_file_mod, len(files))
        
        # test that a generated browse report is present in the success directory
        if self.expected_generated_success_browse_report and len(browse_ids) > 0:
            self.assertIn(self.expected_generated_success_browse_report, files)
        
    
    def test_expected_inserted_into_series(self):
        """ Check that the browse is inserted into the dataset series (browse 
        layer.
        """
        
        if (not self.expected_inserted_into_series or
            not self.expected_ingested_browse_ids):
            self.skipTest("No expected browse IDs or dataset series ID given.")
        
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": self.expected_inserted_into_series}
        )
        
        self.assertTrue(dataset_series is not None)
        
        expected_coverage_ids = self.expected_ingested_coverage_ids or self.expected_ingested_browse_ids
        actual_ids = set([c.getCoverageId() for c in dataset_series.getEOCoverages()])
        
        self.assertItemsEqual(expected_coverage_ids, actual_ids)
    
    
    def test_expected_optimized_files(self):
        """ Check that the expected optimized files are created. """
        
        # check that all optimized files are beeing created
        files = self.get_file_list(self.temp_optimized_files_dir)
        self.assertItemsEqual(self.expected_optimized_files, files)
        
    
    def test_deleted_storage_files(self):
        """ Check that the storage files were deleted/moved from the storage
            dir.
        """
        
        if self.expected_deleted_files is None:
            self.skipTest("No expected files given.")
            
        for filename in self.expected_deleted_files:
            self.assertFalse(exists(join(self.temp_storage_dir, filename)))

    
    def test_seed(self):
        """ Check that the seeding is done. """
        # TODO: implement
        self.skipTest("Not yet implemented.")
        pass
    
    
    def test_model_counts(self):
        """ Check that the models have been created correctly. """
        
        for model, value in self.model_counts.items():
            self.assertEqual(value[0] + 1, value[1],
                             "Model '%s' count mismatch." % model)


class IngestReplaceTestCaseMixIn(IngestTestCaseMixIn):
    """ Test case mixin for testing replacement tests. """
    
    request_before_replace = None
    request_before_replace_file = None
    
    expected_num_replaced = 1
    
    def test_expected_num_replaced(self):
        """ Check the returned number in the ingest result. """
        
        result = IngestResult(self.response.content)
        self.assertEqual(self.expected_num_replaced, result.actually_replaced)
        
    
    def test_model_counts(self):
        """ Check that no orphaned data entries are left in the database. """
        
        for model, value in self.model_counts.items():
            self.assertEqual(value[0], value[1],
                             "Model '%s' count mismatch." % model)
    
    def test_delete_previous_file(self):
        """ Check that the previous raster file is deleted. """
        
        # TODO: implement
        self.skipTest("Not yet implemented.")
        pass


class RasterMixIn(object):
    """ Test case mix-in to test (GDAL-)raster files. """
    raster_file = None
    
    def open_raster(self, dirname=None, raster_file=None):
        """ Convenience function to open a GDAL dataset. """
        
        dirname = dirname or self.temp_optimized_files_dir
        raster_file = raster_file or self.raster_file
        
        filename = join(dirname, raster_file)
        
        try:
            return gdal.Open(filename)
        except RuntimeError:
            self.fail("Raster file '%s' is not present." % filename)


class OverviewMixIn(RasterMixIn):
    expected_overview_count = None
    
    def test_overview_count(self):
        if self.expected_overview_count is None:
            self.skipTest("No default overview count given.")
        
        ds = self.open_raster()
        ovr_count = ds.GetRasterBand(1).GetOverviewCount()
        self.assertEqual(self.expected_overview_count, ovr_count)


class CompressionMixIn(RasterMixIn):
    expected_compression = None
    
    def test_compression(self):
        ds = self.open_raster()
        md = ds.GetMetadata_Dict("IMAGE_STRUCTURE")
        self.assertEqual(self.expected_compression, md.get("COMPRESSION"))


class BandCountMixIn(RasterMixIn):
    expected_band_count = None
    
    def test_band_count(self):
        if self.expected_band_count is None:
            self.skipTest("No expected band count given.")
            
        ds = self.open_raster()
        self.assertEqual(self.expected_band_count, ds.RasterCount)


class HasColorTableMixIn(BandCountMixIn):
    
    expected_band_count = 1
    
    def test_color_table(self):
        ds = self.open_raster()
        band = ds.GetRasterBand(1)
        self.assertEqual(gdal.GCI_PaletteIndex, band.GetColorInterpretation())
        self.assertNotEqual(None, band.GetColorTable())


class ExtentMixIn(RasterMixIn):
    expected_extent = None
    
    def test_extent(self):
        if self.expected_extent is None:
            self.skipTest("No expected extent given.")
        
        ds = self.open_raster()
        self.assertEqual(self.expected_extent, getExtentFromRectifiedDS(ds))


class SizeMixIn(RasterMixIn):
    expected_size = None # tuple (sizex, sizey)
    
    def test_size(self):
        if self.expected_size is None:
            self.skipTest("No expected size given.")
        
        ds = self.open_raster()
        self.assertEqual(self.expected_size, (ds.RasterXSize, ds.RasterYSize))


class ProjectionMixIn(RasterMixIn):
    expected_projection_srid = None # WKT format
    
    def test_projection(self):
        if self.expected_projection_srid is None:
            self.skipTest("No expected projection given.")
        
        ds = self.open_raster()
        exp_sr = osr.SpatialReference()
        exp_sr.ImportFromEPSG(self.expected_projection_srid)
        
        sr = osr.SpatialReference()
        sr.ImportFromWkt(ds.GetProjectionRef())
        
        self.assertTrue(exp_sr.IsSame(sr))


class IngestFailureTestCaseMixIn(IngestTestCaseMixIn):
    """ Test failures in ingestion. """
    
    expected_failed_browse_ids = ()
    expected_failed_files = ()
    expect_exception = False
    
    expected_generated_failure_browse_report = None
    
    
    def test_expected_failed(self):
        """ Check that the failed ingestion is declared in the result. Also
        check that the files are copied into the failure directory.
        """
        
        if not self.expect_exception:
            result = IngestResult(self.get_response())
            failed_ids = [record[0] for record in result.failed]
            
            self.assertItemsEqual(self.expected_failed_browse_ids, failed_ids)
            
            # make sure that the generated browse report is present aswell
            expected_failed_files = list(self.expected_failed_files)
            expected_failed_files.append(self.expected_generated_failure_browse_report)
            
            # get file list of failure_dir and compare the count
            files = self.get_file_list(self.temp_failure_dir)
            self.assertItemsEqual(expected_failed_files, files)
        else:
            pass # TODO


    def test_model_counts(self):
        """ Check that database state is the same as before. """
        
        for model, value in self.model_counts.items():
            self.assertEqual(value[0], value[1],
                             "Model '%s' count mismatch." % model)
