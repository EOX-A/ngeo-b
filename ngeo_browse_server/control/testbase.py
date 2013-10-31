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

import sys
from os import walk, remove, chmod, stat, utime
from stat import S_IEXEC
from os.path import join, exists, dirname
import tempfile
import shutil
from cStringIO import StringIO
from lxml import etree
from django.utils import log
import logging
import numpy
import re
import tarfile
import sqlite3
from ConfigParser import ConfigParser
import time
from urlparse import urlparse

from osgeo import gdal, osr
from django.conf import settings
from django.test.client import Client, FakePayload
from django.core.management import execute_from_command_line
from django.template.loader import render_to_string
from django.utils import simplejson as json
from eoxserver.resources.coverages import models as eoxs_models
from eoxserver.resources.coverages.geo import getExtentFromRectifiedDS
from eoxserver.processing.preprocessing.util import create_mem_copy
from eoxserver.core.util.timetools import isoformat

from ngeo_browse_server.config import get_ngeo_config, reset_ngeo_config
from ngeo_browse_server.config import models
from ngeo_browse_server.control.ingest import safe_makedirs
from ngeo_browse_server.control.ingest.config import (
    INGEST_SECTION, 
)
from ngeo_browse_server.mapcache import models as mapcache_models
from ngeo_browse_server.mapcache.config import SEED_SECTION 
from ngeo_browse_server.control.migration.package import (
    SEC_CACHE, BROWSE_LAYER_NAME, SEC_OPTIMIZED
)
from ngeo_browse_server.control.control.config import CTRL_SECTION


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
    """ Base Mixin for ngEO test cases. """
    
    fixtures = ["initial_rangetypes.json", "ngeo_browse_layer.json", 
                "eoxs_dataset_series.json", "ngeo_mapcache.json"]
    
    # pointing to the actual data directory. Will be copied to a temporary directory
    storage_dir = "data/reference_test_data"
    multi_db = True
    
    surveilled_model_classes = (
        models.Browse,
        eoxs_models.RectifiedDataset,
        mapcache_models.Time
    )
    
    copy_to_optimized = () # list of filenames to be copied to the optimized dir
    
    default_configuration = {
        (CTRL_SECTION, "instance_id"): "instance",
        (CTRL_SECTION, "controller_config_path"): "conf/controller.conf",
        (INGEST_SECTION, "optimized_files_postfix"): "_proc",
        (INGEST_SECTION, "compression"): "LZW",
        (INGEST_SECTION, "jpeg_quality"): "75",
        (INGEST_SECTION, "zlevel"): "6",
        (INGEST_SECTION, "tiling"): "true",
        (INGEST_SECTION, "overviews"): "true",
        (INGEST_SECTION, "overview_resampling"): "NEAREST",
        (INGEST_SECTION, "overview_levels"): None,
        (INGEST_SECTION, "overview_minsize"): "256",
        (INGEST_SECTION, "color_index"): "false",
        (INGEST_SECTION, "footprint_alpha"): "true",
        (INGEST_SECTION, "delete_on_success"): "true",
        (INGEST_SECTION, "leave_original"): "false",
        # storage_dir, success_dir, failure_dir, optimized_files_dir, and 
        # seed_command are set automatically in setUp_files.
    }
    
    configuration = {}
    
    # check the number of DS, Browse and Time models in the database
    model_counts = {}
    
    # in case of certain tests (replace, export, etc.) we need to ingest 
    # something during setUp
    request_before_test = None
    request_before_test_file = None
    args_before_test = ()
    
    def setUp(self):
        logger.info("Starting Test Case: %s" % self.__class__.__name__)
        super(BaseTestCaseMixIn, self).setUp()
        self.setUp_files()
        self.setUp_config()
        
        # ingest browse(s) to be replaced, exported, etc.
        self.setUp_ingest()
        
        # wrap the ingestion with model counter to check if operation added or 
        # deleted expected number of models
        self.add_counts(*self.surveilled_model_classes)
        self.response = self.execute()
        self.add_counts(*self.surveilled_model_classes)
    
    def tearDown(self):
        super(BaseTestCaseMixIn, self).tearDown()
        self.tearDown_files()
        self.model_counts.clear()
        
        # reset the config settings
        reset_ngeo_config()
        logger.info("Finished Test Case: %s" % self.__class__.__name__)
    
    def setUp_files(self):
        # create a temporary storage directory, copy the reference test data
        # into it, and point the control.ingest.storage_dir to this location
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
        
        # setup mapcache config/files as retrieved from template
        self.temp_mapcache_dir = tempfile.mkdtemp() + "/"
        db_file = settings.DATABASES["mapcache"]["TEST_NAME"]
        mapcache_config_file = join(self.temp_mapcache_dir, "mapcache.xml")
        
        with open(mapcache_config_file, "w+") as f:
            f.write(render_to_string("test_control/mapcache.xml",
                                     {"mapcache_dir": self.temp_mapcache_dir,
                                      "mapcache_test_db": db_file,
                                      "browse_layers": models.BrowseLayer.objects.all(),
                                      "base_url": getattr(self, "live_server_url",
                                                          "http://localhost/browse")}))
        
        config.set(SEED_SECTION, "config_file", mapcache_config_file)
        config.set("mapcache", "tileset_root", self.temp_mapcache_dir)
        
        # setup mapcache dummy seed command
        seed_command_file = tempfile.NamedTemporaryFile(delete=False)
        seed_command_file.write("#!/bin/sh\nexit 0")
        self.seed_command = seed_command_file.name
        seed_command_file.close()
        st = stat(self.seed_command)
        chmod(self.seed_command, st.st_mode | S_IEXEC)
        
        config.set(SEED_SECTION, "seed_command", self.seed_command)
    
    def setUp_config(self):
        # set up default config and specific config
        
        config = get_ngeo_config()
        for configuration in (self.default_configuration, self.configuration):
            for (section, option), value in configuration.items():
                if not config.has_section(section):
                    config.add_section(section)
                if value is not None:
                    config.set(section, option, value)
                else:
                    config.remove_option(section, option)
    
    def setUp_ingest(self):
        self.before_test_files = 0
        
        # get request from file
        if self.request_before_test_file is not None:
            filename = join(settings.PROJECT_DIR, "data", self.request_before_test_file)
            with open(filename) as f:
                self.request_before_test = str(f.read())
        
        # execute request or command
        if self.request_before_test is not None:
            self.execute(self.request_before_test)
            self.before_test_files = 1
            # one browse report (no browse because "delete_on_success" is true)
        elif self.args_before_test:
            self.execute(self.args_before_test)
    
    def tearDown_files(self):
        # remove the created temporary directories
        for d in (self.temp_storage_dir, self.temp_optimized_files_dir,
                  self.temp_success_dir, self.temp_failure_dir,
                  self.temp_mapcache_dir):
            shutil.rmtree(d)
        remove(self.seed_command)
    
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
    """ Base class for testing the HTTP interface. """
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


class HttpTestCaseMixin(HttpMixIn):
    """ Holds status code and comparison to expected response test. """

    def test_expected_status(self):
        """ Check the status code of the response. """
        self.assertEqual(self.expected_status, self.response.status_code)
    
    
    def test_expected_response(self):
        """ Check that the response is equal to the provided one if present. """
        if self.expected_response is None:
            self.skipTest("No expected response given.")
        
        self.assertEqual(self.expected_response, self.response.content)


class HttpMultipleMixIn(object):
    """ Base class for testing the HTTP interface. """
    requests = ()
    request_files = ()
    url = "/ingest/"
    
    expected_status = 200
    expected_response = None
    
    def get_requests(self):
        for request in self.requests:
            yield request
        
        for request_file in self.request_files:
            filename = join(settings.PROJECT_DIR, "data", request_file)
            with open(filename) as f:
                yield str(f.read())
    
    
    def execute(self, requests=None, url=None):
        if not url:
            url = self.url
        
        if not requests:
            requests = self.get_requests()
        
        client = Client()        
        
        responses = []
        for request in requests:
            responses.append(client.post(url, request, "text/xml"))
        return responses


class CliMixIn(object):
    """ Base class for testing the command line interface. """
    command = "ngeo_ingest_browse_report"
    args = ()
    kwargs = {}
    
    expect_failure = False
    
    def execute(self, args=None):
        # construct command line parameters
        if not args:
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
        # return stout
        return self.response[0]


class CliFailureMixIn(CliMixIn):
    """ Common base class for CLI failure test cases. """
    
    expected_failure_msg = None
    
    def get_response(self):
        # return sterr
        return self.response[1]

    def test_failure_msg(self):
        """ Check the failure message. """
        self.assertEqual(self.expected_failure_msg, self.get_response())


class BaseInsertTestCaseMixIn(BaseTestCaseMixIn):
    """ Common base class for insertion (ingestion or import) test cases.
    """
    
    expected_ingested_browse_ids = ()
    expected_ingested_coverage_ids = None # Defaults to expected_ingested_browse_ids
    expected_inserted_into_series = None
    expected_optimized_files = ()
    expected_tiles = None     # dict. key: zoom level, value: count
    save_optimized_files = False
    
    def test_expected_inserted_browses(self):
        """ Check that the expected browses are inserted. """
        
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
            try:
                eoxs_models.RectifiedDataset.objects.get(identifier=coverage_id)
            except eoxs_models.RectifiedDataset.DoesNotExist:
                self.fail("RectifiedDataset record does not exist.")
        
    
    def test_expected_inserted_into_series(self):
        """ Check that the browses are inserted into the corresponding browse layer. """
        
        if (not self.expected_inserted_into_series or
            not self.expected_ingested_browse_ids):
            self.skipTest("No expected browse IDs or dataset series ID given.")
        
        try:
            dataset_series = eoxs_models.DatasetSeries.objects.get(
                identifier=self.expected_inserted_into_series
            )
        except eoxs_models.DatasetSeries.DoesNotExist:
            self.fail(
                "DatasetSeries with ID '%s' does not exist." 
                % self.expected_inserted_into_series
            )

        expected_coverage_ids = self.expected_ingested_coverage_ids or self.expected_ingested_browse_ids
        actual_ids = set([c.identifier for c in dataset_series])
        
        self.assertItemsEqual(expected_coverage_ids, actual_ids)
    
    
    def test_expected_optimized_files(self):
        """ Check that the expected optimized files are created. """
        
        # check that all optimized files are beeing created
        files = self.get_file_list(self.temp_optimized_files_dir)
        
        if self.save_optimized_files:
            save_dir = join(settings.PROJECT_DIR, "results/ingest/")
            safe_makedirs(dirname(save_dir))
            for path, _, filenames in walk(self.temp_optimized_files_dir):
                for file_to_save in filenames:
                    shutil.copy(join(path, file_to_save), save_dir) 
        
        self.assertItemsEqual(self.expected_optimized_files, files)
    
    
    def test_model_counts(self):
        """ Check that the models have been created correctly. """
        
        num_ingested_models = len(self.expected_ingested_coverage_ids or
                                  self.expected_ingested_browse_ids)
        for model, value in self.model_counts.items():
            self.assertEqual(value[0] + num_ingested_models, value[1],
                             "Model '%s' count mismatch." % model)


class IngestTestCaseMixIn(BaseInsertTestCaseMixIn):
    """ Mixin for ngEO ingest test cases. Checks whether or not the browses with
    the specified IDs have been correctly registered.  
    """
    
    expected_deleted_files = None
    
    
    def test_deleted_storage_files(self):
        """ Check that the storage files were deleted/moved from the storage dir. """
        
        if self.expected_deleted_files is None:
            self.skipTest("No expected files to delete given.")
            
        for filename in self.expected_deleted_files:
            self.assertFalse(exists(join(self.temp_storage_dir, filename)))
    
    
    def test_expected_inserted_browses(self):
        """ Check that the expected browses are ingested and the files correctly moved. """
        super(IngestTestCaseMixIn, self).test_expected_inserted_browses()
        
        browse_ids = self.expected_ingested_browse_ids
        
        browse_report_file_mod = 0
        if len(browse_ids) > 0:
            # if at least one browse was successfully ingested, a browse report
            # must also be present.
            browse_report_file_mod = 1
        
        # test that the correct number of files was moved/created in the success
        # directory
        # note that successfully ingested browse images are not moved but 
        # deleted (configuration "delete_on_success")
        files = self.get_file_list(self.temp_success_dir)
        self.assertEqual(browse_report_file_mod + self.before_test_files, len(files))


class ImportTestCaseMixIn(BaseInsertTestCaseMixIn):
    """ Test case mixin for import tests.
    """
    
    command = "ngeo_import"


class ImportReplaceTestCaseMixin(ImportTestCaseMixIn):
    """ Test case mixin for import replacement tests. """
    
    expected_deleted_optimized_files = None
    
    expected_num_replaced = 1
    
    def test_model_counts(self):
        """ Check that no orphaned data entries are left in the database. """
        
        for model, value in self.model_counts.items():
            self.assertEqual(value[0], value[1],
                             "Model '%s' count mismatch." % model)
    
    def test_delete_previous_file(self):
        """ Check that the previous raster file is deleted. """
        
        if self.expected_deleted_optimized_files is None:
            self.skipTest("No expected optimized files to delete given.")
            
        for filename in self.expected_deleted_optimized_files:
            self.assertFalse(exists(join(self.temp_optimized_files_dir, filename)))


class DeleteTestCaseMixIn(BaseTestCaseMixIn):
    """ Mixin for ngEO delete test cases. Checks whether or not the browses are
    deleted correctly based on the specified parameters.  
    """
    
    command = "ngeo_delete"
    
    expected_remaining_browses = None
    expected_deleted_files = []

    surveilled_model_classes = (
        models.Browse,
        eoxs_models.RectifiedDataset,
    )
   
    def test_deleted_optimized_files(self):
        """ Check that all optimized files have been deleted. """
        for filename in self.expected_deleted_files:
            self.assertFalse(exists(join(self.temp_optimized_files_dir, filename)), 
                             "Optimized file not deleted.")
            
    def test_browse_deletion(self):
        """ Check that all browses and their corresponding coverages have been deleted. """
        for model, value in self.model_counts.items():
            self.assertEqual(value[1], self.expected_remaining_browses,
                             "Model '%s' count is not expected value." % model)


class SeedTestCaseMixIn(BaseTestCaseMixIn):
    """ Mixin for ngEO seed test cases. Checks whether or not the browses with
    the specified IDs have been correctly seeded in MapCache.  
    """

    if exists("/usr/bin/mapcache_seed"):
        seed_command = "/usr/bin/mapcache_seed"
    elif exists("/usr/local/bin/mapcache_seed"):
        seed_command = "/usr/local/bin/mapcache_seed"
    else:
        raise IOError("MapCache seed command not found.")
    
    configuration = {
        (SEED_SECTION, "seed_command"): seed_command,
    }

    def test_seed(self):
        """ Check that the seeding is done correctly. """
        
        db_filename = join(self.temp_mapcache_dir, 
                           self.expected_inserted_into_series + ".sqlite")
        
        # check that the file exists
        self.assertTrue(exists(db_filename))
        
        # expected tiles, check the zoomlevel counts        
        if self.expected_tiles:
            with sqlite3.connect(db_filename) as connection:
                cur = connection.cursor()
                
                cur.execute("SELECT z, count(z) FROM tiles GROUP BY z;")
            
                tiles = dict(cur.fetchall())
                self.assertEqual(self.expected_tiles, tiles)
                
                any_filled = False
                vsimem_path = "/vsimem/img.png"
                
                cur = connection.cursor()
                cur.execute("SELECT data FROM tiles;")
                for (tile,) in cur.fetchall():
                    # create in-memory file and open it with gdal 
                    gdal.FileFromMemBuffer(vsimem_path, str(tile))
                    ds = gdal.Open(vsimem_path)
                    data = ds.ReadAsArray()
                    
                    # check if it contains any data; (0,0,0,0) is empty
                    not_empty = numpy.any(data)
                    any_filled = not_empty or any_filled
                    
                    # delete the file when done
                    gdal.Unlink(vsimem_path)
                    if any_filled: break;
            
                if not any_filled:
                    self.fail("All tiles are empty.")


class SeedMergeTestCaseMixIn(SeedTestCaseMixIn):
    expected_seeded_areas = () # iterable of 2-tuples: start_time, end_time
    
    def test_seed_merge(self):
        """ Checks the `Time` models. Checks that the tilesets only contain 
        tiles that are in the correct time span.
        """
        
        from ngeo_browse_server.mapcache.models import Time
        
        times = [(t.start_time, t.end_time) for t in Time.objects.all()]
        
        self.assertItemsEqual(self.expected_seeded_areas, times)
    
        db_filename = join(self.temp_mapcache_dir, 
                       self.expected_inserted_into_series + ".sqlite")
        
        expected_timespans = ["%s/%s" % (isoformat(area[-2]), isoformat(area[-1]))
                              for area in self.expected_seeded_areas]
        
        with sqlite3.connect(db_filename) as connection:
            cur = connection.cursor()
            cur.execute("SELECT DISTINCT dim FROM tiles;")
            timespans = [row[0] for row in cur.fetchall()]
            self.assertItemsEqual(expected_timespans, timespans)
            

class IngestReplaceTestCaseMixIn(IngestTestCaseMixIn):
    """ Test case mixin for testing replacement tests. """
    
    expected_deleted_optimized_files = None
    
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
        
        if self.expected_deleted_optimized_files is None:
            self.skipTest("No expected optimized files to delete given.")
            
        for filename in self.expected_deleted_optimized_files:
            self.assertFalse(exists(join(self.temp_optimized_files_dir, filename)))


class RasterMixIn(object):
    """ Test case mix-in to test the optimized (GDAL-)raster files. """
    raster_file = None
    
    save_to_file = None
    
    def open_raster(self, dir_name=None, raster_file=None):
        """ Convenience function to open a GDAL dataset. """
        
        dir_name = dir_name or self.temp_optimized_files_dir
        raster_file = raster_file or self.raster_file
        
        filename = join(dir_name, raster_file)
        
        if self.save_to_file:
            save_filename = join(settings.PROJECT_DIR, self.save_to_file)
            safe_makedirs(dirname(save_filename))
            shutil.copy(filename, save_filename)
        
        try:
            return gdal.Open(filename)
        except RuntimeError:
            self.fail("Raster file '%s' is not present." % filename)


class WMSRasterMixIn(RasterMixIn):
    """ Test case mix-in to test WMS raster responses instead of the optimized 
    files.
    """
    
    wms_request = None
    
    def open_raster(self):
        # dispatch wms request
        response = self.client.get(self.wms_request)
        
        if self.save_to_file:
            save_filename = join(settings.PROJECT_DIR, self.save_to_file)
            safe_makedirs(dirname(save_filename))
            with open(save_filename, "w+") as f:
                f.write(response.content)
        
        if response.status_code != 200:
            self.fail("WMS received response with status '%d'"
                      % response.status_code) 
        
        filename = '/vsimem/wms_temp'
        
        try:
            gdal.FileFromMemBuffer(filename, response.content)
            ds = gdal.Open(filename, gdal.GA_ReadOnly)
        
        finally:
            gdal.Unlink(filename)
        
        return ds


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
    expected_projection_srid = None # EPSG integer
    
    def test_projection(self):
        if self.expected_projection_srid is None:
            self.skipTest("No expected projection given.")
        
        ds = self.open_raster()
        exp_sr = osr.SpatialReference()
        exp_sr.ImportFromEPSG(self.expected_projection_srid)
        
        sr = osr.SpatialReference()
        sr.ImportFromWkt(ds.GetProjectionRef())
        
        self.assertTrue(exp_sr.IsSame(sr))


class StatisticsMixIn(RasterMixIn):
    expected_statistics = []
    maxDiff = None
    
    def test_statistics(self):
        if not self.expected_statistics:
            self.skipTest("No expected statistics given.")
        
        # Use in-memory dataset here to not create a statistics metadata file on
        # the disc.
        ds = create_mem_copy(self.open_raster())
        self.assertEqual(len(self.expected_statistics), ds.RasterCount)
        
        statistics = []
        for index in range(1, ds.RasterCount + 1):
            names = ("min", "max", "mean", "stddev", "checksum")
            
            band = ds.GetRasterBand(index)
            stats = band.ComputeStatistics(False) + [band.Checksum()]
            statistics.append(dict(zip(names, stats)))
            
        self.assertEqual(self.expected_statistics, statistics)


class IngestFailureTestCaseMixIn(BaseTestCaseMixIn):
    """ Test failures in ingestion. """
    
    expected_failed_browse_ids = ()
    expected_failed_files = ()
    expect_exception = False
    
    expected_generated_failure_browse_report = None
    
    
    def test_expected_failed(self):
        """ Check that the failed ingestion is declared in the result and the 
        files are moved to the failure directory.
        """
        
        if not self.expect_exception:
            result = IngestResult(self.get_response())
            failed_ids = [record[0] for record in result.failed]
            
            self.assertItemsEqual(self.expected_failed_browse_ids, failed_ids)
            
            # make sure that the generated browse report is present aswell
            expected_failed_files = list(self.expected_failed_files)
            #expected_failed_files.append(self.expected_generated_failure_browse_report)
            
            # find the generated browse report by regex and remove it from the
            # list of files in the directory. Fail, if it was not found.
            files = self.get_file_list(self.temp_failure_dir)
            if self.expected_generated_failure_browse_report:
                for idx, filename in enumerate(files):
                    if re.match(self.expected_generated_failure_browse_report, filename):
                        del files[idx]
                        break
                else:
                    self.fail("Generated failure browse report was not found.")
            
            # get file list of failure_dir and compare the count
            
            self.assertItemsEqual(expected_failed_files, files)
        else:
            pass # nothing to test in case of an early exception


    def test_model_counts(self):
        """ Check that database state is the same as before. """
        
        for model, value in self.model_counts.items():
            self.assertEqual(value[0], value[1],
                             "Model '%s' count mismatch." % model)


class ExportTestCaseMixIn(BaseTestCaseMixIn):
    """ Mixin for export tests.
    """
    
    command = "ngeo_export"
    
    expected_exported_browses = ()
    expected_cache_tiles = None
    
    @property
    def args(self):
        return ("--output", self.temp_export_file)
    
    def setUp_files(self):
        super(ExportTestCaseMixIn, self).setUp_files()
        self.temp_export_file = tempfile.mktemp(suffix=".tar.gz")
    
    def tearDown_files(self):
        super(ExportTestCaseMixIn, self).tearDown_files()
        remove(self.temp_export_file)
    
    def test_archive_content(self):
        """ Test that the archive contains the expected files.
        """
        
        try:
            archive = tarfile.open(self.temp_export_file)
        except tarfile.TarError, e:
            self.fail(str(e))
        
        try:
            archive.getmember(BROWSE_LAYER_NAME)
        except KeyError:
            self.fail("Archive does not contain %s." % BROWSE_LAYER_NAME)
        
        for browse_id in self.expected_exported_browses:
            try:
                archive.getmember(join(SEC_OPTIMIZED, browse_id + ".tif"))
                archive.getmember(join(SEC_OPTIMIZED, browse_id + ".wkb"))
            except KeyError:
                self.fail("Archive does not contain %s.tif or %s.wkb."
                          % (browse_id, browse_id))
        
        if self.expected_cache_tiles is not None:
            cache_tiles = 0
            for member in archive:
                if member.name.startswith(SEC_CACHE) and member.isfile():
                    cache_tiles += 1
            
            self.assertEqual(self.expected_cache_tiles, cache_tiles)

        archive.close()
            
            

class TestLogHandler(logging.Handler):
    """
    A handler class which sends log strings to a wx object
    """
    def __init__(self):
        """
        Initialize the handler
        @param wxDest: the destination object to post the event to 
        @type wxDest: wx.Window
        """
        logging.Handler.__init__(self)
        self.level = logging.DEBUG
        self.logs = {}

    def flush(self):
        "does nothing for this handler"


    def emit(self, record):
        """
        Emit a record.

        """
        msg = self.format(record)
        self.logs.setdefault(record.levelno, []).append(msg)
        

class LoggingTestCaseMixIn(object):
    
    expected_logs = {}
    logging_config = {}
    
    def setUp(self):
        super(LoggingTestCaseMixIn, self).setUp()
        self.log_handler = TestLogHandler()
        log.dictConfig(self.logging_config)
        logging.getLogger("ngeo_browse_server").addHandler(self.log_handler)
    
    def tearDown(self):
        super(LoggingTestCaseMixIn, self).tearDown()
        log.dictConfig(settings.LOGGING)
        logging.getLogger("ngeo_browse_server").removeHandler(self.log_handler)

            
    def test_expected_logs(self):
        
        logs = dict((level, len(entries)) 
                    for level, entries in self.log_handler.logs.items())
        
        all_levels = (
            logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, 
            logging.CRITICAL
        )
        
        for level in all_levels:
            logs.setdefault(level, 0)
        
        self.assertEqual(self.expected_logs, logs)


class ControlTestCaseMixIn(BaseTestCaseMixIn):
    """ Test mix in for controller server interfaces
    """

    controller_config = None
    status_config = None

    url = "/controllerServer/"
    request = None
    request_file = None
    ip_address = None
    method = "post"
    expected_response = None


    def setUp_files(self):
        super(ControlTestCaseMixIn, self).setUp_files()
        self.temp_controller_server_config = join(tempfile.gettempdir(), "controller.conf")
        self.temp_status_config = join(tempfile.gettempdir(), "status.conf")

        if self.controller_config is not None:
            with open(self.temp_controller_server_config, "w+") as f:
                f.write(self.controller_config)

        if self.status_config is not None:
            with open(self.temp_status_config, "w+") as f:
                f.write(self.status_config)


    def setUp_config(self):
        super(ControlTestCaseMixIn, self).setUp_config()
        config = get_ngeo_config()
        config.set(CTRL_SECTION, "controller_config_path", self.temp_controller_server_config)
        config.set(CTRL_SECTION, "status_config_path", self.temp_status_config)

    def tearDown_files(self):
        if exists(self.temp_controller_server_config):
            remove(self.temp_controller_server_config)

        if exists(self.temp_status_config):
            remove(self.temp_status_config)

    def execute(self, request=None, url=None):
        if not url:
            url = self.url

        extra = {}
        if self.ip_address:
            extra['REMOTE_ADDR'] = self.ip_address

        client = Client()
        if self.method != "get":
            # Django 1.4 is not able to handle DELETE requests with payload.
            # workaround here:
            extra.update({
                'wsgi.input': FakePayload(self.request),
                'CONTENT_LENGTH': len(self.request),
                'CONTENT_TYPE': "text/json",
                'PATH_INFO': client._get_path(urlparse(url)),
                'REQUEST_METHOD': self.method.upper()
            })
            return client.request(**extra)
        else:
            return client.get(url, **extra);

    def get_request(self):
        if self.request is not None:
            return self.request
        
        elif self.request_file:
            filename = join(settings.PROJECT_DIR, "data", self.request_file)
            with open(filename) as f:
                return str(f.read())

    def get_response(self):
        return json.loads(self.response.content)

    def test_expected_response(self):
        """ Check that the response is equal to the provided one if present. """
        if self.expected_response is None:
            self.skipTest("No expected response given.")
        
        if isinstance(self.expected_response, basestring):
            content = self.response.content
        else:
            content = self.get_response()
        self.assertEqual(self.expected_response, content)


class RegisterTestCaseMixIn(ControlTestCaseMixIn):
    
    expected_controller_config = None

    def test_controller_config(self):
        """Test that the controller config is present as expected and contains 
        the correct values.
        """

        self.assertEqual((self.expected_controller_config is not None), exists(self.temp_controller_server_config))
        if self.expected_controller_config is not None:
            conf = ConfigParser()
            from ngeo_browse_server.control.control.config import CONTROLLER_SERVER_SECTION as section
            with open(self.temp_controller_server_config) as f:
                conf.readfp(f)
            for key, value in self.expected_controller_config.items():
                self.assertEqual(value, conf.get(section, key))


class UnregisterTestCaseMixIn(ControlTestCaseMixIn):
    method = "delete" # TODO: delete is problematic when using Django < 1.5

    expected_controller_config_deleted = True

    def test_config_deleted(self):
        self.assertNotEqual(
            self.expected_controller_config_deleted,
            exists(self.temp_controller_server_config)
        )


class StatusTestCaseMixIn(ControlTestCaseMixIn):
    method = "get"
    url = "/status/"
    
    def get_request(self):
        return {}

    def get_response(self):
        response = super(StatusTestCaseMixIn, self).get_response()
        if "timestamp" in response:
            del response["timestamp"]
        return response


class ControlLogMixIn(ControlTestCaseMixIn):
    method = "get"
    url = "/log/"

    log_files = [] # list of tuples: (filename, date, content)

    maxDiff = None

    def setUp_files(self):
        super(ControlLogMixIn, self).setUp_files()

        self.temp_log_dir = tempfile.mkdtemp()
        for log_file, date, content in self.log_files:
            filename = join(self.temp_log_dir, log_file)
            with open(join(self.temp_log_dir, log_file), "w+") as f:
                f.write(content)

            timestamp = time.mktime(date.timetuple())
            utime(filename, (timestamp, timestamp))

    def tearDown_files(self):
        shutil.rmtree(self.temp_log_dir)

    @property 
    def configuration(self):
        return {(CTRL_SECTION, "report_log_files"): join(self.temp_log_dir, "*")}


class LogListMixIn(ControlLogMixIn):
    pass


class LogFileMixIn(ControlLogMixIn):
    pass
