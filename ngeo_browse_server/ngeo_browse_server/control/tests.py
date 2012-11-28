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
from os import walk
from os.path import join, exists
import tempfile
import shutil
from cStringIO import StringIO
from lxml import etree
import logging

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.core.management import execute_from_command_line
from eoxserver.core.system import System
from eoxserver.resources.coverages import models as eoxs_models

from ngeo_browse_server.config import get_ngeo_config, reset_ngeo_config
from ngeo_browse_server.config import models
from ngeo_browse_server.mapcache import models as mapcache_models


logger = logging.getLogger(__name__)

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
    
    # pointing to the actual data directory. Will be copied to a temporary directory
    storage_dir = "data/reference_test_data"
    multi_db = True
    
    surveilled_model_classes = (
        models.Browse,
        eoxs_models.RectifiedDatasetRecord,
        mapcache_models.Time,
        mapcache_models.Source
    )
    
    def setUp(self):
        super(BaseTestCaseMixIn, self).setUp()
        self.setUp_files()
        
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
        
        # streamline configuration
        config.set(section, "delete_on_success", "false")
        config.set(section, "leave_original", "false")
    
    
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
    expected_response = ""
    
    def get_request(self):
        if self.request:
            return self.request
        
        elif self.request_file:
            filename = join(settings.PROJECT_DIR, "data", self.request_file);
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
    
    fixtures = ["initial_rangetypes.json", "ngeo_browse_layer.json", 
                "eoxs_dataset_series.json", "ngeo_mapcache.json"]
    expected_ingested_browse_ids = ()
    expected_ingested_coverage_ids = None
    expected_inserted_into_series = None
    expected_optimized_files = ()
    expected_deleted_files = None
    
    
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
            
            coverage_wrapper = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": coverage_id}
            )
            self.assertTrue(coverage_wrapper is not None)
        
        files = self.get_file_list(self.temp_success_dir)
        self.assertEqual(len(browse_ids), len(files))
        
    
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
        
        
        # TODO: binary comparison/metadata comparison of images
    
    
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
        
        for key, value in self.model_counts.items():
            self.assertEqual(value[0], value[1],
                             "Model '%s' count mismatch: %d != %d." 
                             % (key, value[0], value[1]))
    
    def test_delete_previous_file(self):
        """ Check that the previous raster file is deleted. """
        
        # TODO: implement
        self.skipTest("Not yet implemented.")
        pass


class IngestFailureTestCaseMixIn(IngestTestCaseMixIn):
    """ Test failures in ingestion. """
    
    expected_failed_browse_ids = ()
    expected_failed_files = ()
    
    def test_expected_failed(self):
        """ Check that the failed ingestion is declared in the result. Also
        check that the files are copied into the failure directory.
        """
        
        result = IngestResult(self.get_response())
        failed_ids = [record[0] for record in result.failed]
        
        self.assertItemsEqual(self.expected_failed_browse_ids, failed_ids)
        
        # get file list of failure_dir and compare the count
        files = self.get_file_list(self.temp_failure_dir)
        self.assertItemsEqual(self.expected_failed_files, files)

#===============================================================================
# actual test cases
#===============================================================================

class IngestRegularGrid(IngestTestCaseMixIn, HttpMixIn, TestCase):
    storage_dir = "data"
    
    expected_ingested_browse_ids = ("ASAR",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775_proc.tif']
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>SAR</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>ASAR</rep:browseIdentifier>
        <rep:fileName>ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tiff</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:regularGrid>
            <rep:colNodeNumber>11</rep:colNodeNumber>
            <rep:rowNodeNumber>10</rep:rowNodeNumber>
            <rep:colStep>56.7</rep:colStep>
            <rep:rowStep>54</rep:rowStep>
            <rep:coordList>-33.039026 22.301754 -32.940249 21.858518 -32.839872 21.416104 -32.737996 20.974925 -32.634647 20.535039 -32.530560 20.099457 -32.423501 19.658868 -32.315686 19.222430 -32.206376 18.787042 -32.095583 18.352726</rep:coordList>
            <rep:coordList>-31.984922 17.925622 -33.397168 22.188887 -33.298089 21.743944 -33.197388 21.299842 -33.095169 20.856998 -32.991456 20.415469 -32.886988 19.978276 -32.779523 19.536078 -32.671284 19.098063 -32.561531 18.661121</rep:coordList>
            <rep:coordList>-32.450277 18.225272 -32.339140 17.796681 -33.755205 22.075213 -33.655818 21.628534 -33.554789 21.182717 -33.452221 20.738179 -33.348139 20.294979 -33.243284 19.856150 -33.135407 19.412314 -33.026740 18.972696</rep:coordList>
            <rep:coordList>-32.916538 18.534174 -32.804815 18.096769 -32.693198 17.666665 -34.113133 21.960709 -34.013433 21.512264 -33.912071 21.064702 -33.809149 20.618442 -33.704692 20.173543 -33.599445 19.733050 -33.491150 19.287550</rep:coordList>
            <rep:coordList>-33.382048 18.846303 -33.271391 18.406174 -33.159194 17.967187 -33.047090 17.535547 -34.470954 21.845378 -34.370937 21.395137 -34.269236 20.945801 -34.165954 20.497790 -34.061117 20.051163 -33.955472 19.608978</rep:coordList>
            <rep:coordList>-33.846754 19.161786 -33.737211 18.718883 -33.626093 18.277122 -33.513416 17.836527 -33.400819 17.403326 -34.828661 21.729172 -34.728321 21.277104 -34.626275 20.825964 -34.522628 20.376173 -34.417405 19.927790</rep:coordList>
            <rep:coordList>-34.311357 19.483886 -34.202209 19.034974 -34.092219 18.590387 -33.980634 18.146967 -33.867470 17.704737 -33.754375 17.269949 -35.186259 21.612104 -35.085590 21.158180 -34.983195 20.705206 -34.879177 20.253605</rep:coordList>
            <rep:coordList>-34.773562 19.803437 -34.667105 19.357784 -34.557521 18.907124 -34.447078 18.460826 -34.335020 18.015720 -34.221363 17.571829 -34.107762 17.135429 -35.543742 21.494141 -35.442739 21.038329 -35.339988 20.583490</rep:coordList>
            <rep:coordList>-35.235594 20.130049 -35.129581 19.678066 -35.022709 19.230636 -34.912683 18.778199 -34.801780 18.330163 -34.689243 17.883343 -34.575086 17.437765 -34.460973 16.999727 -35.901108 21.375264 -35.799766 20.917532</rep:coordList>
            <rep:coordList>-35.696654 20.460797 -35.591877 20.005485 -35.485461 19.551657 -35.378166 19.102421 -35.267692 18.648179 -35.156323 18.198375 -35.043300 17.749814 -34.928636 17.302521 -34.814005 16.862819 -36.259107 21.262123</rep:coordList>
            <rep:coordList>-36.157233 20.801477 -36.053622 20.342135 -35.948361 19.884418 -35.841461 19.428326 -35.733683 18.976948 -35.622707 18.520618 -35.510829 18.068811 -35.397282 17.618307 -35.282080 17.169124 -35.166903 16.727605</rep:coordList>
        </rep:regularGrid>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
    </rep:browse>
</rep:browseReport>"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>ASAR</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Ingest Footprint browses
#===============================================================================
    
class IngestFootprintBrowse(IngestTestCaseMixIn, HttpMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    
    expected_ingested_browse_ids = ("b_id_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100722_213840_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100722_213840.jpg']
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_1</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestFootprintBrowse2(IngestTestCaseMixIn, HttpMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100731_103315.xml"
    
    expected_ingested_browse_ids = ("b_id_2",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100731_103315_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100731_103315.jpg']
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_2</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestFootprintBrowse3(IngestTestCaseMixIn, HttpMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100813_102453.xml"
    
    expected_ingested_browse_ids = ("b_id_5",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100813_102453_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100813_102453.jpg']
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_5</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Ingest into layer OPTICAL
#===============================================================================

class IngestFootprintBrowse4(IngestTestCaseMixIn, HttpMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100719_105257.xml"
    
    expected_ingested_browse_ids = ("b_id_9",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100719_105257_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100719_105257.jpg']
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_9</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestFootprintBrowse5(IngestTestCaseMixIn, HttpMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100719_213253.xml"
    
    expected_ingested_browse_ids = ("b_id_10",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100719_213253_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100719_213253.jpg']
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_10</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestFootprintBrowse6(IngestTestCaseMixIn, HttpMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100722_101606.xml"
    
    expected_ingested_browse_ids = ("b_id_11",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100722_101606_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100722_101606.jpg']
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_11</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Arbitrary ingests
#===============================================================================

class IngestBrowseNoID(IngestTestCaseMixIn, HttpMixIn, TestCase):
    
    expected_ingested_browse_ids = (None,)
    expected_ingested_coverage_ids = ("TEST_OPTICAL_20100722101606000000_20100722101722000000",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100722_101606_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100722_101606.jpg']
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:fileName>ATS_TOA_1P_20100722_101606.jpg</rep:fileName>
        <rep:imageType>Jpeg</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="5">
            <rep:colRowList>0 0 128 0 128 129 0 129 0 0</rep:colRowList>
            <rep:coordList>52.94 3.45 51.65 10.65 47.28 8.41 48.51 1.82 52.94 3.45</rep:coordList>
        </rep:footprint>
        <rep:startTime>2010-07-22T10:16:06Z</rep:startTime>
        <rep:endTime>2010-07-22T10:17:22Z</rep:endTime>
    </rep:browse>
</rep:browseReport>
"""
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>None</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestBrowseSpecialID(IngestTestCaseMixIn, HttpMixIn, TestCase):
    
    expected_ingested_browse_ids = ("some:special:id",)
    expected_ingested_coverage_ids = ("TEST_OPTICAL_20100722101606000000_20100722101722000000",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100722_101606_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100722_101606.jpg']
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>some:special:id</rep:browseIdentifier>
        <rep:fileName>ATS_TOA_1P_20100722_101606.jpg</rep:fileName>
        <rep:imageType>Jpeg</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="5">
            <rep:colRowList>0 0 128 0 128 129 0 129 0 0</rep:colRowList>
            <rep:coordList>52.94 3.45 51.65 10.65 47.28 8.41 48.51 1.82 52.94 3.45</rep:coordList>
        </rep:footprint>
        <rep:startTime>2010-07-22T10:16:06Z</rep:startTime>
        <rep:endTime>2010-07-22T10:17:22Z</rep:endTime>
    </rep:browse>
</rep:browseReport>
"""
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>some:special:id</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Ingest a browse report with multiple browses inside
#===============================================================================

class IngestFootprintBrowseGroup(IngestTestCaseMixIn, HttpMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"
    
    expected_ingested_browse_ids = ("b_id_6", "b_id_7", "b_id_8")
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_WS__0P_20100719_101023_proc.tif',
                                'ASA_WS__0P_20100722_101601_proc.tif',
                                'ASA_WS__0P_20100725_102231_proc.tif']
    expected_deleted_files = ['ASA_WS__0P_20100719_101023.jpg',
                              'ASA_WS__0P_20100722_101601.jpg',
                              'ASA_WS__0P_20100725_102231.jpg']

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>3</bsi:toBeReplaced>
        <bsi:actuallyInserted>3</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_6</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
        <bsi:briefRecord>
            <bsi:identifier>b_id_7</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
        <bsi:briefRecord>
            <bsi:identifier>b_id_8</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Ingest a browse report which includes a replacement of a previous browse
#===============================================================================

class IngestFootprintBrowseReplace(IngestReplaceTestCaseMixIn, HttpMixIn, TestCase):
    fixtures = IngestReplaceTestCaseMixIn.fixtures + ["browse_ASA_IM__0P_20100807_101327.json"]
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327_new.xml"
    
    expected_num_replaced = 1
    
    expected_ingested_browse_ids = ("b_id_3",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100807_101327_new_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100807_101327_new.jpg']
    
    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>0</bsi:actuallyInserted>
        <bsi:actuallyReplaced>1</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_3</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Ingest Failure tests
#===============================================================================

class IngestFailureNoInputFile(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    request_file = "test_data/BrowseReport_FAILURE.xml" 

    @property
    def expected_response(self):
        return """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>partial</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>0</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>RuntimeError</bsi:exceptionCode>
                <bsi:exceptionMessage>`%s/does_not_exist.tiff&#39; does not exist in the file system,
and is not recognised as a supported dataset name.
</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
""" % self.temp_storage_dir


class IngestFailureIDStartsWithNumber(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("11_id_starts_with_number",)
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>11_id_starts_with_number</rep:browseIdentifier>
        <rep:fileName>ATS_TOA_1P_20100722_101606.jpg</rep:fileName>
        <rep:imageType>Jpeg</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="5">
            <rep:colRowList>0 0 128 0 128 129 0 129 0 0</rep:colRowList>
            <rep:coordList>52.94 3.45 51.65 10.65 47.28 8.41 48.51 1.82 52.94 3.45</rep:coordList>
        </rep:footprint>
        <rep:startTime>2010-07-22T10:16:06Z</rep:startTime>
        <rep:endTime>2010-07-22T10:17:22Z</rep:endTime>
    </rep:browse>
</rep:browseReport>
"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>partial</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>0</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>11_id_starts_with_number</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>ValidationError</bsi:exceptionCode>
                <bsi:exceptionMessage>{&#39;id&#39;: [u&#39;This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops.&#39;]}</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureFootprintNoCircle(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>ATS_TOA_1P_20100722_101606.jpg</rep:fileName>
        <rep:imageType>Jpeg</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="5">
            <rep:colRowList>0 0 128 0 128 129 0 129</rep:colRowList>
            <rep:coordList>52.94 3.45 51.65 10.65 47.28 8.41 48.51 1.82</rep:coordList>
        </rep:footprint>
        <rep:startTime>2010-07-22T10:16:06Z</rep:startTime>
        <rep:endTime>2010-07-22T10:17:22Z</rep:endTime>
    </rep:browse>
</rep:browseReport>"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>partial</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>0</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>The last value of the footprint is not equal to the first.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureUnknownReferenceSystem(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>ATS_TOA_1P_20100722_101606.jpg</rep:fileName>
        <rep:imageType>Jpeg</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:999999</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="5">
            <rep:colRowList>0 0 128 0 128 129 0 129 0 0</rep:colRowList>
            <rep:coordList>52.94 3.45 51.65 10.65 47.28 8.41 48.51 1.82 52.94 3.45</rep:coordList>
        </rep:footprint>
        <rep:startTime>2010-07-22T10:16:06Z</rep:startTime>
        <rep:endTime>2010-07-22T10:17:22Z</rep:endTime>
    </rep:browse>
</rep:browseReport>"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>partial</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>0</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>RuntimeError</bsi:exceptionCode>
                <bsi:exceptionMessage>EPSG PCS/GCS code 999999 not found in EPSG support files.  Is this a valid
EPSG coordinate system?</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureEndBeforeStart(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>ATS_TOA_1P_20100722_101606.jpg</rep:fileName>
        <rep:imageType>Jpeg</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="5">
            <rep:colRowList>0 0 128 0 128 129 0 129 0 0 </rep:colRowList>
            <rep:coordList>52.94 3.45 51.65 10.65 47.28 8.41 48.51 1.82 52.94 3.45</rep:coordList>
        </rep:footprint>
        <rep:startTime>2010-07-22T10:16:06Z</rep:startTime>
        <rep:endTime>2009-07-22T10:17:22Z</rep:endTime>
    </rep:browse>
</rep:browseReport>"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>partial</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>0</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>ValidationError</bsi:exceptionCode>
                <bsi:exceptionMessage>{&#39;__all__&#39;: [u&#39;Start time may not be more recent than end time.&#39;]}</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


#===============================================================================
# Command line ingestion test cases
#===============================================================================

class IngestFromCommand(IngestTestCaseMixIn, CliMixIn, TestCase):
    args = (join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_IM__0P_20100807_101327.xml"),)
    
    expected_ingested_browse_ids = ("b_id_3",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ("ASA_IM__0P_20100807_101327_proc.tif",)
    expected_deleted_files = ['ASA_IM__0P_20100807_101327.jpg']


# TODO: test optimization features

