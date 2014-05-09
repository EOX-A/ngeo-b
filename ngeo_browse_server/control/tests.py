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

from os.path import join
from textwrap import dedent
import logging
from datetime import date
from SocketServer import TCPServer, ThreadingMixIn
from BaseHTTPServer import BaseHTTPRequestHandler
import threading

from django.conf import settings
from django.test import TestCase, TransactionTestCase, LiveServerTestCase
from django.utils.dateparse import parse_datetime

from ngeo_browse_server import get_version
from ngeo_browse_server.config import models
from ngeo_browse_server.control.testbase import (
    BaseTestCaseMixIn, HttpTestCaseMixin, HttpMixIn, CliMixIn, CliFailureMixIn,
    IngestTestCaseMixIn, SeedTestCaseMixIn, IngestReplaceTestCaseMixIn, 
    IngestMergeTestCaseMixIn, OverviewMixIn, CompressionMixIn, BandCountMixIn, 
    HasColorTableMixIn, ExtentMixIn, SizeMixIn, ProjectionMixIn, 
    StatisticsMixIn, WMSRasterMixIn, IngestFailureTestCaseMixIn, 
    DeleteTestCaseMixIn, ExportTestCaseMixIn, ImportTestCaseMixIn, 
    ImportReplaceTestCaseMixin, SeedMergeTestCaseMixIn, HttpMultipleMixIn, 
    LoggingTestCaseMixIn, RegisterTestCaseMixIn, UnregisterTestCaseMixIn, 
    StatusTestCaseMixIn, LogListMixIn, LogFileMixIn, ConfigMixIn,
    ComponentControlTestCaseMixIn, ConfigurationManagementMixIn,
    GenerateReportMixIn
)
from ngeo_browse_server.control.ingest.config import (
    INGEST_SECTION
)
from ngeo_browse_server.control.control.notification import notify


#===============================================================================
# Ingest ModelInGeoTiff browse test cases
#===============================================================================

class IngestModelInGeotiffBrowse(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.xml"
    
    expected_ingested_browse_ids = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    expected_inserted_into_series = "TEST_MER_FRS"
    expected_optimized_files = ['MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_proc.tif']
    expected_deleted_files = ['MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.tif']
    save_optimized_files = True
    
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
            <bsi:identifier>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedModelInGeotiffBrowse(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.xml"
    
    expected_inserted_into_series = "TEST_MER_FRS"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64, 5: 128, 6: 256}


class IngestModelInGeotiffBrowseGoogleMercator(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_GOOGLE_MERCATOR.xml"
    
    expected_ingested_browse_ids = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_MERCATOR",)
    expected_inserted_into_series = "TEST_GOOGLE_MERCATOR"
    expected_optimized_files = ['MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_proc.tif']
    expected_deleted_files = ['MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.tif']
    
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
            <bsi:identifier>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_MERCATOR</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedModelInGeotiffBrowseGoogleMercator(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_GOOGLE_MERCATOR.xml"
    
    expected_inserted_into_series = "TEST_GOOGLE_MERCATOR"
    expected_tiles = {0: 1, 1: 4, 2: 16, 3: 64, 4: 64, 5: 64, 6: 128}


#===============================================================================
# Ingest Rectified browse test cases
#===============================================================================

class IngestRectifiedBrowse(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data/"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo.xml"
    
    expected_ingested_browse_ids = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    expected_inserted_into_series = "TEST_MER_FRS"
    expected_optimized_files = ['MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo_proc.tif']
    expected_deleted_files = ['MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo.tif']
    save_optimized_files = True
    
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
            <bsi:identifier>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedRectifiedBrowse(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data/test_data/"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo.xml"
    
    expected_inserted_into_series = "TEST_MER_FRS"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64, 5: 128, 6: 256}


#===============================================================================
# Ingest Regular Grid browse test cases
#===============================================================================

class IngestRegularGridBrowse(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.xml"
    
    expected_ingested_browse_ids = ("ASAR",)
    expected_inserted_into_series = "TEST_ASA_WSM"
    expected_optimized_files = ['ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775_proc.tif']
    expected_deleted_files = ['ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tif']
    save_optimized_files = True

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

class SeedRegularGridBrowse(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.xml"
    
    expected_inserted_into_series = "TEST_ASA_WSM"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64}

class IngestRegularGridBrowse2(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/feed_test_data"
    request_file = "feed_test_data/BrowseReport.xml"
    
    expected_ingested_browse_ids = ("a20120101T043724405923",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['quick-look_proc.tif']
    expected_deleted_files = ['quick-look.png']

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
            <bsi:identifier>a20120101T043724405923</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedRegularGridBrowse2(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data/feed_test_data"
    request_file = "feed_test_data/BrowseReport.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64}


#===============================================================================
# Ingest Footprint browse test cases
#===============================================================================
    
class IngestFootprintBrowse(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    
    expected_ingested_browse_ids = ("b_id_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100722_213840_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100722_213840.jpg']
    save_optimized_files = True

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

class SeedFootprintBrowse(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class IngestFootprintBrowse2(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
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

class SeedFootprintBrowse2(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100731_103315.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class IngestFootprintBrowse3(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
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

class SeedFootprintBrowse3(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100813_102453.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class IngestFootprintBrowse7(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/aiv_test_data"
    request_file = "aiv_test_data/BrowseReport.xml"
    
    expected_ingested_browse_ids = ("NGEO-FEED-VTC-0040",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['NGEO-FEED-VTC-0040_proc.tif']
    expected_deleted_files = ['NGEO-FEED-VTC-0040.jpg']
    
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
            <bsi:identifier>NGEO-FEED-VTC-0040</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedFootprintBrowse7(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data/aiv_test_data"
    request_file = "aiv_test_data/BrowseReport.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64}


#===============================================================================
# Ingest into layer OPTICAL
#===============================================================================

class IngestFootprintBrowse4(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
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

class SeedFootprintBrowse4(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100719_105257.xml"
    
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class IngestFootprintBrowse5(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
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

class SeedFootprintBrowse5(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100719_213253.xml"
    
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class IngestFootprintBrowse6(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
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

class SeedFootprintBrowse6(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100722_101606.xml"
    
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64}


#===============================================================================
# Arbitrary ingests and corner cases
#===============================================================================

class IngestBrowseNoID(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100722_101606_noid.xml"
    
    expected_ingested_browse_ids = (None,)
    expected_ingested_coverage_ids = ("TEST_OPTICAL_20100722101606000000_20100722101722000000",)
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
            <bsi:identifier>None</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedBrowseNoID(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100722_101606_noid.xml"
    
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64}

class IngestBrowseSpecialID(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100722_101606_specialid.xml"
    
    expected_ingested_browse_ids = ("some:special:id",)
    expected_ingested_coverage_ids = ("TEST_OPTICAL_20100722101606000000_20100722101722000000",)
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
            <bsi:identifier>some:special:id</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedBrowseSpecialID(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100722_101606_specialid.xml"
    
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64}


class IngestBrowseFilenameStartsWithNumber(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    
    expected_ingested_browse_ids = ("identifier",)
    expected_ingested_coverage_ids = ("identifier",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['20120101T091526510-20120101T091714560_D_T-XI0B_proc.tif']
    expected_deleted_files = ['20120101T091526510-20120101T091714560_D_T-XI0B.jpg']
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" version="1.1">
  <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
  <rep:dateTime>2013-01-29T16:41:12.630821</rep:dateTime>
  <rep:browseType>SAR</rep:browseType>
  <rep:browse>
    <rep:browseIdentifier>identifier</rep:browseIdentifier>
    <rep:fileName>20120101T091526510-20120101T091714560_D_T-XI0B.jpg</rep:fileName>
    <rep:imageType>Jpeg</rep:imageType>
    <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier>
    <rep:footprint nodeNumber="7">
      <rep:colRowList>0 0 100 0 100 472 100 944 0 944 0 472 0 0</rep:colRowList>
      <rep:coordList>50.44 14.38 50.33 15.41 47.07 14.56 43.95 13.79 44.07 12.87 47.18 13.59 50.44 14.38</rep:coordList>
    </rep:footprint>
    <rep:startTime>2012-01-01T09:15:26.510000</rep:startTime>
    <rep:endTime>2012-01-01T09:17:14.560000</rep:endTime>
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
            <bsi:identifier>identifier</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestBrowseSubfolderFilename(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    
    expected_ingested_browse_ids = ("identifier",)
    expected_ingested_coverage_ids = ("identifier",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['browse_proc.tif']
    expected_deleted_files = ['subfolder/browse.jpg']

    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" version="1.1">
  <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
  <rep:dateTime>2013-01-29T16:41:12.630821</rep:dateTime>
  <rep:browseType>SAR</rep:browseType>
  <rep:browse>
    <rep:browseIdentifier>identifier</rep:browseIdentifier>
    <rep:fileName>subfolder/browse.jpg</rep:fileName>
    <rep:imageType>Jpeg</rep:imageType>
    <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier>
    <rep:footprint nodeNumber="7">
      <rep:colRowList>0 0 100 0 100 472 100 944 0 944 0 472 0 0</rep:colRowList>
      <rep:coordList>50.44 14.38 50.33 15.41 47.07 14.56 43.95 13.79 44.07 12.87 47.18 13.59 50.44 14.38</rep:coordList>
    </rep:footprint>
    <rep:startTime>2012-01-01T09:15:26.510000</rep:startTime>
    <rep:endTime>2012-01-01T09:17:14.560000</rep:endTime>
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
            <bsi:identifier>identifier</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestModelInGeotiffBrowseCompicatedFootprint(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    """See issue #59"""
    storage_dir = "data/test_data"
    
    expected_ingested_browse_ids = ("DWH_MG2_SIRI_ADD_010a_40",)
    expected_ingested_coverage_ids = ("DWH_MG2_SIRI_ADD_010a_40",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['218658_3358114_browse.jpg_r_proc.tif']
    expected_deleted_files = ['218658_3358114_browse.jpg_r.tif']

    request = """\
<?xml version="1.0" encoding="utf-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" version="1.1">
  <rep:responsibleOrgName>RapidEye</rep:responsibleOrgName>
  <rep:dateTime>2012-09-18T15:30:44+00:00</rep:dateTime>
  <rep:browseType>SAR</rep:browseType>
  <rep:browse>
    <rep:browseIdentifier>DWH_MG2_SIRI_ADD_010a_40</rep:browseIdentifier>
    <rep:fileName>218658_3358114_browse.jpg_r.tif</rep:fileName>
    <rep:imageType>TIFF</rep:imageType>
    <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier>
    <rep:modelInGeotiff>true</rep:modelInGeotiff>
    <rep:startTime>2012-08-19T11:00:27+00:00</rep:startTime>
    <rep:endTime>2012-08-19T11:00:32+00:00</rep:endTime>
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
            <bsi:identifier>DWH_MG2_SIRI_ADD_010a_40</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestBrowseCrossesDateline(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_file = "test_data/BrowseReport_crosses_dateline.xml"
    storage_dir = "data/test_data"
    
    expected_ingested_browse_ids = ("_20120101T022322540-20120101T030036350_D_T-AA0B",)
    expected_ingested_coverage_ids = ("_20120101T022322540-20120101T030036350_D_T-AA0B",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['_20120101T022322540-20120101T030036350_D_T-AA0B_proc.tif']
    expected_deleted_files = ['_20120101T022322540-20120101T030036350_D_T-AA0B.jpg']
    
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
            <bsi:identifier>_20120101T022322540-20120101T030036350_D_T-AA0B</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Ingest a browse with internal GCPs
#===============================================================================

class IngestBrowseInternalGCPs(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_file = "gcps/1396863968337_BrowseServerIngest_1396863968062_input.xml"
    storage_dir = "data/gcps"
    
    expected_ingested_browse_ids = ("ID_DODWH_MG2_CORE_09DM010001_1",)
    expected_ingested_coverage_ids = ("ID_DODWH_MG2_CORE_09DM010001_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ID_DEIMOS01-v2_DE0028bfp_L3R_proc.tif']
    expected_deleted_files = ['ID_DEIMOS01-v2_DE0028bfp_L3R.tif']
    
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
            <bsi:identifier>ID_DODWH_MG2_CORE_09DM010001_1</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

#===============================================================================
# Ingest a browse report with multiple browses inside
#===============================================================================

class IngestFootprintBrowseGroup(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
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

class SeedFootprintBrowseGroup(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 6, 1: 24, 2: 96, 3: 384, 4: 384}

#===============================================================================
# Ingest a browse report which includes a replacement of a previous browse
#===============================================================================

class IngestFootprintBrowseReplace(IngestReplaceTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_before_test_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327.xml"
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327_new.xml"
    
    expected_num_replaced = 1
    
    expected_ingested_browse_ids = ("b_id_3",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100807_101327_new_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100807_101327_new.jpg']
    expected_deleted_optimized_files = ['ASA_IM__0P_20100807_101327.tif']
    
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


class IngestFootprintBrowseMerge(IngestMergeTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_before_test_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327.xml"
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327_new_merge.xml"
    
    expected_num_replaced = 1
    
    expected_ingested_browse_ids = ("b_id_3",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100807_101327_new_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100807_101327_new.jpg']
    expected_deleted_optimized_files = ['ASA_IM__0P_20100807_101327.tif']
    
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
# Ingest partial (some success and some failure) tests
#===============================================================================

class IngestFootprintBrowseGroupPartial(IngestTestCaseMixIn, HttpTestCaseMixin, TransactionTestCase):
    request_file = "reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group_partial.xml"
    
    expected_ingested_browse_ids = ("b_id_6", "b_id_8")
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_WS__0P_20100719_101023_proc.tif',
                                'ASA_WS__0P_20100725_102231_proc.tif']
    expected_deleted_files = ['ASA_WS__0P_20100719_101023.jpg',
                              'ASA_WS__0P_20100725_102231.jpg']

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>partial</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>3</bsi:toBeReplaced>
        <bsi:actuallyInserted>2</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>b_id_6</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
        <bsi:briefRecord>
            <bsi:identifier>7_FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>ValidationError</bsi:exceptionCode>
                <bsi:exceptionMessage>Browse Identifier &#39;7_FAILURE&#39; not valid: &#39;This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops.&#39;.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
        <bsi:briefRecord>
            <bsi:identifier>b_id_8</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class SeedFootprintBrowseGroupPartial(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group_partial.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 4, 1: 16, 2: 64, 3: 256, 4: 256}



#===============================================================================
# Seed merge tests
#===============================================================================

class SeedMerge1(SeedMergeTestCaseMixIn, HttpMultipleMixIn, LiveServerTestCase):
    """ Simple merging of two time windows. """
    
    request_files = ("merge_test_data/br_merge_1.xml", 
                     "merge_test_data/br_merge_2.xml"
                     )
    
    storage_dir = "data/merge_test_data"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}
    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:38:40Z"),
         parse_datetime("2010-07-22T21:40:38Z"))
    ]
    
    
class SeedMerge2(SeedMergeTestCaseMixIn, HttpMultipleMixIn, LiveServerTestCase):
    """ Merging 2 time windows with a third. """
    
    request_files = ("merge_test_data/br_merge_1.xml", 
                     "merge_test_data/br_merge_3.xml",
                     "merge_test_data/br_merge_2.xml",
                     )
    
    storage_dir = "data/merge_test_data"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}
    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:38:40Z"),
         parse_datetime("2010-07-22T21:42:38Z"))
    ]
    

class SeedMerge3(SeedMergeTestCaseMixIn, HttpMultipleMixIn, LiveServerTestCase):
    """ Splitting consquent time window in seperate. """
    
    request_files = ("merge_test_data/br_merge_1.xml", 
                     "merge_test_data/br_merge_2.xml",
                     "merge_test_data/br_merge_3.xml",
                     "merge_test_data/br_merge_3_replace.xml",
                     )
    
    storage_dir = "data/merge_test_data"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 4, 1: 16, 2: 64, 3: 192, 4: 192}
    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:38:40Z"),
         parse_datetime("2010-07-22T21:40:38Z")),
        (parse_datetime("2010-07-22T21:46:38Z"),
         parse_datetime("2010-07-22T21:48:38Z"))
    ]


class SeedMerge4(SeedMergeTestCaseMixIn, HttpMultipleMixIn, LiveServerTestCase):
    """ Splitting consquent time window in two seperate but with slight overlap.
    """
    
    request_files = ("merge_test_data/br_merge_2.xml",
                     "merge_test_data/br_merge_3.xml",
                     "merge_test_data/br_merge_3_replace_2.xml",
                     )
    
    storage_dir = "data/merge_test_data"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 4, 1: 16, 2: 64, 3: 192, 4: 192}
    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:39:00Z"),
         parse_datetime("2010-07-22T21:40:38Z")),
        (parse_datetime("2010-07-22T21:42:38Z"),
         parse_datetime("2010-07-22T21:44:38Z")),
    ]


class SeedMerge5(SeedMergeTestCaseMixIn, HttpMultipleMixIn, LiveServerTestCase):
    """ Merging two time windows with a replacement.
    """
    
    request_files = ("merge_test_data/br_merge_1.xml",
                     "merge_test_data/br_merge_3.xml",
                     "merge_test_data/br_merge_3_replace_3.xml",
                     )
    
    storage_dir = "data/merge_test_data"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}
    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:36:40Z"),
         parse_datetime("2010-07-22T21:39:38Z"))
    ]

#===============================================================================
# Ingest Failure tests
#===============================================================================

class IngestFailureNoInputFile(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_generated_failure_browse_report = "SAR_EOX_20121002093000000000_(.*).xml"

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
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Input file &#39;%s/does_not_exist.tiff&#39; does not exist.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
""" % self.temp_storage_dir


#===============================================================================
# Invalid Requests
#===============================================================================


class IngestFailureInvalidXML(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = ""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Could not parse request XML. Error was: &#39;Start tag expected, &#39;&lt;&#39; not found, line 1, column 1&#39;.</bsi:exceptionMessage>
</bsi:ingestException>
"""

class IngestFailureInvalidRootTag(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = "<someRoot></someRoot>"

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Invalid root tag &#39;someRoot&#39;. Expected one of &#39;(&#39;{http://ngeo.eo.esa.int/schema/browse/ingestion}ingestBrowse&#39;, &#39;{http://ngeo.eo.esa.int/schema/browseReport}browseReport&#39;)&#39;.</bsi:exceptionMessage>
</bsi:ingestException>
"""


class IngestFailureMissingElement(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
</rep:browseReport>
"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Could not find required element rep:browseType/text().</bsi:exceptionMessage>
</bsi:ingestException>
"""


class IngestFailureUnexpectedNumber(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>XXX</rep:browseType>
    <rep:browseType>YYY</rep:browseType>
</rep:browseReport>
"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Found unexpected number (2) of elements rep:browseType/text(). Expected 1.</bsi:exceptionMessage>
</bsi:ingestException>
"""


class IngestFailureExpectedAtMost(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>MER_FRS</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>XXX</rep:browseIdentifier>
        <rep:browseIdentifier>YYY</rep:browseIdentifier>
        <rep:fileName>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo.tif</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:rectifiedBrowse>
            <rep:coordList>32.1902500 8.4784500 46.2686450 25.4101500</rep:coordList>
        </rep:rectifiedBrowse>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
    </rep:browse>
</rep:browseReport>
"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Expected at most one element of rep:browseIdentifier/text().</bsi:exceptionMessage>
</bsi:ingestException>
"""


class IngestFailureMissingGeospatialReference(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>MER_FRS</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>XXX</rep:browseIdentifier>
        <rep:fileName>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo.tif</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
    </rep:browse>
</rep:browseReport>
"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Missing geo-spatial reference type.</bsi:exceptionMessage>
</bsi:ingestException>
"""


#===============================================================================
# Validation Errors
#===============================================================================


class IngestFailureIDStartsWithNumber(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TransactionTestCase):
    expected_failed_browse_ids = ("11_id_starts_with_number",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    
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
                <bsi:exceptionMessage>Browse Identifier &#39;11_id_starts_with_number&#39; not valid: &#39;This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops.&#39;.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureEndBeforeStart(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    
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


class IngestFailureInvalidFilename(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TransactionTestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = []
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"

    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>#?.jpg</rep:fileName>
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
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>ValidationError</bsi:exceptionCode>
                <bsi:exceptionMessage>[u&#39;Filenames must only contain letters, digits, hyphens, underscores, colons, slashes, or full stops.&#39;]</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


#===============================================================================
# Ingestion Exceptions
#===============================================================================

class IngestFailureBrowseTypeDoesNotExist(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>DOESNOTEXIST</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>NGEO-FEED-VTC-0040.jpg</rep:fileName>
        <rep:imageType>PNG</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="7">
            <rep:colRowList>0 0 7 0 0 0</rep:colRowList>
            <rep:coordList>48.46 16.1001 48.48 16.1 48.46 16.1001</rep:coordList>
        </rep:footprint>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
    </rep:browse>
</rep:browseReport>
"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
    <bsi:exceptionMessage>Browse layer with browse type &#39;DOESNOTEXIST&#39; does not exist.</bsi:exceptionMessage>
</bsi:ingestException>
"""



class IngestFailureWrongRelativeFilename(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TransactionTestCase):
    expected_failed_browse_ids = ("identifier",)
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>identifier</rep:browseIdentifier>
        <rep:fileName>../input_filename.jpg</rep:fileName>
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
            <bsi:identifier>identifier</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Input path &#39;../input_filename.jpg&#39; points to an invalid location.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureWrongAbsoluteFilename(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TransactionTestCase):
    expected_failed_browse_ids = ("identifier",)
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>identifier</rep:browseIdentifier>
        <rep:fileName>/etc/absolute_filename.jpg</rep:fileName>
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
            <bsi:identifier>identifier</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Input path &#39;/etc/absolute_filename.jpg&#39; points to an invalid location.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureFootprintNoCircle(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    
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


class IngestFailureInvalidReferenceSystem(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TransactionTestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"

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
        <rep:referenceSystemIdentifier>INVALID</rep:referenceSystemIdentifier> 
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
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Given referenceSystemIdentifier &#39;INVALID&#39; not valid.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureUnknownReferenceSystem(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    
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
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Given referenceSystemIdentifier &#39;EPSG:999999&#39; not valid.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureRAWReferenceSystem(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    
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
        <rep:referenceSystemIdentifier>RAW</rep:referenceSystemIdentifier> 
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
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Given referenceSystemIdentifier &#39;RAW&#39; not valid for a &#39;footprintBrowse&#39;.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureContradictingIDs(IngestFailureTestCaseMixIn, IngestReplaceTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_before_test_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327.xml"
    
    expected_num_replaced = 0
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ASA_IM__0P_20100807_101327_new.jpg"]
    expected_generated_failure_browse_report = "SAR_ESA_20121002093000000000_(.*).xml"    
    
    expected_ingested_browse_ids = ()
    expected_optimized_files = ['ASA_IM__0P_20100807_101327_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100807_101327_new.jpg']
    expected_deleted_optimized_files = []
    
    # disable those tests as they are not valid for exception tests
    test_expected_inserted_browses = None
    test_expected_inserted_into_series = None
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>SAR</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>ASA_IM__0P_20100807_101327_new.jpg</rep:fileName>
        <rep:imageType>Jpeg</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="5">
            <rep:colRowList>0 0 494 0 494 861 0 861 0 0</rep:colRowList>
            <rep:coordList>51.8 2.45 51.58 3.99 49.89 3.36 50.1 1.87 51.8 2.45</rep:coordList>
        </rep:footprint>
        <rep:startTime>2010-08-07T10:13:37Z</rep:startTime>
        <rep:endTime>2010-08-07T10:14:06Z</rep:endTime>
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
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Existing browse with same start and end time does not have the same browse ID as the one to ingest.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureNoValidTransformException(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/aiv_test_data"
    
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["NGEO-FEED-VTC-0040.jpg"]
    expected_generated_failure_browse_report = "SAR_ESA_20121002093000000000_(.*).xml"
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.1">
    <rep:responsibleOrgName>ESA</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>SAR</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>NGEO-FEED-VTC-0040.jpg</rep:fileName>
        <rep:imageType>PNG</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:footprint nodeNumber="7">
            <rep:colRowList>0 0 7 0 0 0</rep:colRowList>
            <rep:coordList>48.46 16.1001 48.48 16.1 48.46 16.1001</rep:coordList>
        </rep:footprint>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
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
            <bsi:identifier>FAILURE</bsi:identifier>
            <bsi:status>failure</bsi:status>
            <bsi:error>
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>Could not find a valid transform method.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureInvalidRegularGrid1(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tif"]
    expected_generated_failure_browse_report = "ASA_WSM_EOX_20121002093000000000_(.*).xml"
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>ASA_WSM</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tif</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:regularGrid>
            <rep:colNodeNumber>10</rep:colNodeNumber>
            <rep:rowNodeNumber>11</rep:rowNodeNumber>
            <rep:colStep>53.888888889</rep:colStep>
            <rep:rowStep>56.8</rep:rowStep>
            <rep:coordList>-33.039026 22.301754 -33.397168 22.188887 -33.755205 22.075213 -34.113133 21.960709 -34.470954 21.845378 -34.828661 21.729172 -35.186259 21.612104 -35.543742 21.494141 -35.901108 21.375264 -36.259107 21.262123</rep:coordList>
            <rep:coordList>-32.940249 21.858518 -33.298089 21.743944 -33.655818 21.628534 -34.013433 21.512264 -34.370937 21.395137 -34.728321 21.277104 -35.085590 21.158180 -35.442739 21.038329 -35.799766 20.917532 -36.157233 20.801477</rep:coordList>
            <rep:coordList>-32.839872 21.416104 -33.197388 21.299842 -33.554789 21.182717 -33.912071 21.064702 -34.269236 20.945801 -34.626275 20.825964 -34.983195 20.705206 -35.339988 20.583490 -35.696654 20.460797 -36.053622 20.342135</rep:coordList>
            <rep:coordList>-32.737996 20.974925 -33.095169 20.856998 -33.452221 20.738179 -33.809149 20.618442 -34.165954 20.497790 -34.522628 20.376173 -34.879177 20.253605 -35.235594 20.130049 -35.591877 20.005485 -35.948361 19.884418</rep:coordList>
            <rep:coordList>-32.634647 20.535039 -32.991456 20.415469 -33.348139 20.294979 -33.704692 20.173543 -34.061117 20.051163 -34.417405 19.927790 -34.773562 19.803437 -35.129581 19.678066 -35.485461 19.551657 -35.841461 19.428326</rep:coordList>
            <rep:coordList>-32.530560 20.099457 -32.886988 19.978276 -33.243284 19.856150 -33.599445 19.733050 -33.955472 19.608978 -34.311357 19.483886 -34.667105 19.357784 -35.022709 19.230636 -35.378166 19.102421 -35.733683 18.976948</rep:coordList>
            <rep:coordList>-32.423501 19.658868 -32.779523 19.536078 -33.135407 19.412314 -33.491150 19.287550 -33.846754 19.161786 -34.202209 19.034974 -34.557521 18.907124 -34.912683 18.778199 -35.267692 18.648179 -35.622707 18.520618</rep:coordList>
            <rep:coordList>-32.315686 19.222430 -32.671284 19.098063 -33.026740 18.972696 -33.382048 18.846303 -33.737211 18.718883 -34.092219 18.590387 -34.447078 18.460826 -34.801780 18.330163 -35.156323 18.198375 -35.510829 18.068811</rep:coordList>
            <rep:coordList>-32.206376 18.787042 -32.561531 18.661121 -32.916538 18.534174 -33.271391 18.406174 -33.626093 18.277122 -33.980634 18.146967 -34.335020 18.015720 -34.689243 17.883343 -35.043300 17.749814 -35.397282 17.618307</rep:coordList>
            <rep:coordList>-32.095583 18.352726 -32.450277 18.225272 -32.804815 18.096769 -33.159194 17.967187 -33.513416 17.836527 -33.867470 17.704737 -34.221363 17.571829 -34.575086 17.437765 -34.928636 17.302521 -35.282080 17.169124</rep:coordList>
        </rep:regularGrid>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
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
                <bsi:exceptionMessage>Invalid regularGrid: number of coordinate lists is not equal to the given row node number.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


class IngestFailureInvalidRegularGrid2(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tif"]
    expected_generated_failure_browse_report = "ASA_WSM_EOX_20121002093000000000_(.*).xml"
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>ASA_WSM</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tif</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:regularGrid>
            <rep:colNodeNumber>10</rep:colNodeNumber>
            <rep:rowNodeNumber>11</rep:rowNodeNumber>
            <rep:colStep>53.888888889</rep:colStep>
            <rep:rowStep>56.8</rep:rowStep>
            <rep:coordList>-33.039026 22.301754 -33.397168 22.188887 -33.755205 22.075213 -34.113133 21.960709 -34.470954 21.845378 -34.828661 21.729172 -35.186259 21.612104 -35.543742 21.494141 -35.901108 21.375264</rep:coordList>
            <rep:coordList>-32.940249 21.858518 -33.298089 21.743944 -33.655818 21.628534 -34.013433 21.512264 -34.370937 21.395137 -34.728321 21.277104 -35.085590 21.158180 -35.442739 21.038329 -35.799766 20.917532</rep:coordList>
            <rep:coordList>-32.839872 21.416104 -33.197388 21.299842 -33.554789 21.182717 -33.912071 21.064702 -34.269236 20.945801 -34.626275 20.825964 -34.983195 20.705206 -35.339988 20.583490 -35.696654 20.460797</rep:coordList>
            <rep:coordList>-32.737996 20.974925 -33.095169 20.856998 -33.452221 20.738179 -33.809149 20.618442 -34.165954 20.497790 -34.522628 20.376173 -34.879177 20.253605 -35.235594 20.130049 -35.591877 20.005485</rep:coordList>
            <rep:coordList>-32.634647 20.535039 -32.991456 20.415469 -33.348139 20.294979 -33.704692 20.173543 -34.061117 20.051163 -34.417405 19.927790 -34.773562 19.803437 -35.129581 19.678066 -35.485461 19.551657</rep:coordList>
            <rep:coordList>-32.530560 20.099457 -32.886988 19.978276 -33.243284 19.856150 -33.599445 19.733050 -33.955472 19.608978 -34.311357 19.483886 -34.667105 19.357784 -35.022709 19.230636 -35.378166 19.102421</rep:coordList>
            <rep:coordList>-32.423501 19.658868 -32.779523 19.536078 -33.135407 19.412314 -33.491150 19.287550 -33.846754 19.161786 -34.202209 19.034974 -34.557521 18.907124 -34.912683 18.778199 -35.267692 18.648179</rep:coordList>
            <rep:coordList>-32.315686 19.222430 -32.671284 19.098063 -33.026740 18.972696 -33.382048 18.846303 -33.737211 18.718883 -34.092219 18.590387 -34.447078 18.460826 -34.801780 18.330163 -35.156323 18.198375</rep:coordList>
            <rep:coordList>-32.206376 18.787042 -32.561531 18.661121 -32.916538 18.534174 -33.271391 18.406174 -33.626093 18.277122 -33.980634 18.146967 -34.335020 18.015720 -34.689243 17.883343 -35.043300 17.749814</rep:coordList>
            <rep:coordList>-32.095583 18.352726 -32.450277 18.225272 -32.804815 18.096769 -33.159194 17.967187 -33.513416 17.836527 -33.867470 17.704737 -34.221363 17.571829 -34.575086 17.437765 -34.928636 17.302521</rep:coordList>
            <rep:coordList>-31.984922 17.925622 -32.339140 17.796681 -32.693198 17.666665 -33.047090 17.535547 -33.400819 17.403326 -33.754375 17.269949 -34.107762 17.135429 -34.460973 16.999727 -34.814005 16.862819</rep:coordList>
        </rep:regularGrid>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
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
                <bsi:exceptionMessage>Invalid regularGrid: number of coordinates does not fit given columns number.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestFailureUnsupportedFormat(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    storage_dir = "data/test_data"
    
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["empty.tif"]
    expected_generated_failure_browse_report = "ASA_WSM_EOX_20121002093000000000_(.*).xml"
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>ASA_WSM</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>FAILURE</rep:browseIdentifier>
        <rep:fileName>empty.tif</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:modelInGeotiff>true</rep:modelInGeotiff>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
    </rep:browse>
</rep:browseReport>"""
 
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
                <bsi:exceptionCode>IngestionException</bsi:exceptionCode>
                <bsi:exceptionMessage>`%s/empty.tif&#39; not recognised as a supported file format.
</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
""" % self.temp_storage_dir


#===============================================================================
# Raster test cases
#===============================================================================

    
class IngestRasterOverviewsAutomatic(BaseTestCaseMixIn, HttpMixIn, OverviewMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "overviews"): "true",
        (INGEST_SECTION, "overview_minsize"): "100"
    }
    
    expected_overview_count = 4
    

class IngestRasterOverviewsFixed(BaseTestCaseMixIn, HttpMixIn, OverviewMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "overviews"): "true",
        (INGEST_SECTION, "overview_levels"): "2,4"
    }
    
    expected_overview_count = 2


class IngestRasterNoOverviews(BaseTestCaseMixIn, HttpMixIn, OverviewMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "overviews"): "false"
    }
    
    expected_overview_count = 0

        
class IngestRasterCompression(BaseTestCaseMixIn, HttpMixIn, CompressionMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "compression"): "DEFLATE"
    }
    
    expected_compression = "DEFLATE"


class IngestRasterNoCompression(BaseTestCaseMixIn, HttpMixIn, CompressionMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "compression"): "NONE"
    }
    
    expected_compression = None


class IngestRasterFootprintAlpha(BaseTestCaseMixIn, HttpMixIn, BandCountMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "footprint_alpha"): "true"
    }
    
    expected_band_count = 4


class IngestRasterNoFootprintAlpha(BaseTestCaseMixIn, HttpMixIn, BandCountMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "footprint_alpha"): None
    }
    
    expected_band_count = 3


class IngestRasterColorIndex(BaseTestCaseMixIn, HttpMixIn, HasColorTableMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "color_index"): "true",
        (INGEST_SECTION, "footprint_alpha"): "false",
    }


class IngestRasterExtent(BaseTestCaseMixIn, HttpMixIn, ExtentMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    expected_extent = (-2.7900000000000005, 
                       49.461072913650007, 
                       -0.029483356685718665, 
                       53.079999999999998)


class IngestRasterSize(BaseTestCaseMixIn, HttpMixIn, SizeMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    expected_size = (1177, 1543)


class IngestRasterProjectionEPSG4326(BaseTestCaseMixIn, HttpMixIn, ProjectionMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    expected_projection_srid = 4326


class IngestRasterStatistics(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "2010", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    save_to_file = "results/raster/IngestRasterStatistics.tif"
    
    expected_statistics = [{
        "min": 0.0,
        "max": 255.0,
        "mean": 64.246238253058323,
        "stddev": 76.142837880325871,
        "checksum": 10724
    }, {
        "min": 0.0,
        "max": 255.0,
        "mean": 64.246238253058323,
        "stddev": 76.142837880325871,
        "checksum": 10724
    }, {
        "min": 0.0,
        "max": 255.0,
        "mean": 64.246238253058323,
        "stddev": 76.142837880325871,
        "checksum": 10724
    }, {
        "min": 0.0,
        "max": 255.0,
        "mean": 138.47198216408577,
        "stddev": 127.02702707452059,
        "checksum": 44673
    }]


#===============================================================================
# Raster tests for browses with more than 3 input bands
#===============================================================================


class IngestRasterStatisticsMultipleBands(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml"
    
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_MER_FRS_FULL", "2012", "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_proc.tif"))
    
    expected_statistics = [
        {'max': 255.0, 'checksum': 30191, 'mean': 15.659451199310894, 'stddev': 22.103667727281124, 'min': 0.0},
        {'max': 255.0, 'checksum': 35428, 'mean': 13.540062615955472, 'stddev': 21.258531872828733, 'min': 0.0},
        {'max': 255.0, 'checksum': 16276, 'mean': 13.158705771269547, 'stddev': 21.48301977479764, 'min': 0.0},
        {'max': 255.0, 'checksum': 20036, 'mean': 165.27394480519482, 'stddev': 121.7759380742111, 'min': 0.0} 
    ]


class IngestRasterStatisticsMultipleBandsNoDefinition(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_NO_BANDS.xml"
    
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_MER_FRS_FULL_NO_BANDS", "2012", "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_proc.tif"))
    
    expected_statistics = [
        {'max': 255.0, 'checksum': 33522, 'mean': 17.049554399681952, 'stddev': 22.625493105759691, 'min': 0.0},
        {'max': 255.0, 'checksum': 30191, 'mean': 15.659451199310894, 'stddev': 22.103667727281124, 'min': 0.0},
        {'max': 255.0, 'checksum': 6918, 'mean': 14.176099092234296, 'stddev': 21.602771443516307, 'min': 0.0},
        {'max': 255.0, 'checksum': 20027, 'mean': 165.27394480519482, 'stddev': 121.7759380742111, 'min': 0.0} 
    ]
    

#===============================================================================
# WMS Raster test cases
#===============================================================================

class IngestModelInGeoTiffWMSRaster(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
                       "bbox": ",".join(map(str, (
                            32.1902500,
                            8.4784500,  
                            46.2686450, 
                            25.4101500))),
                       "width": 100,
                       "height": 100,
                    }
                   )
    
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.xml"
    
    save_to_file = "results/wms/IngestModelInGeoTiffWMSRaster.png"
    
    expected_statistics = [
        {'max': 255.0, 'checksum': 10021, 'mean': 40.744900000000001, 'stddev': 41.571134504485194, 'min': 0.0},
        {'max': 255.0, 'checksum': 9487, 'mean': 39.966999999999999, 'stddev': 40.339262648194257, 'min': 0.0},
        {'max': 255.0, 'checksum': 11914, 'mean': 42.195999999999998, 'stddev': 38.414057114551177, 'min': 0.0}
    ]


class IngestRectifiedWMSRaster(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
                       "bbox": ",".join(map(str, (
                            32.1902500,
                            8.4784500,  
                            46.2686450, 
                            25.4101500))),
                       "width": 100,
                       "height": 100,
                    }
                   )

    storage_dir = "data/test_data/"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo.xml"
    
    save_to_file = "results/wms/IngestRectifiedWMSRaster.png"
    
    expected_statistics = [
        {'max': 255.0, 'checksum': 10021, 'mean': 40.744900000000001, 'stddev': 41.571134504485194, 'min': 0.0},
        {'max': 255.0, 'checksum': 9487, 'mean': 39.966999999999999, 'stddev': 40.339262648194257, 'min': 0.0},
        {'max': 255.0, 'checksum': 11914, 'mean': 42.195999999999998, 'stddev': 38.414057114551177, 'min': 0.0}
    ]


class IngestRectifiedFlippedWMSRaster(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
                       "bbox": ",".join(map(str, (
                            32.1902500,
                            8.4784500,
                            46.2686450,
                            25.4101500))),
                       "width": 100,
                       "height": 100,
                    }
                   )

    storage_dir = "data/test_data/"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_nogeo_flipped.xml"

    save_to_file = "results/wms/IngestRectifiedFlippedWMSRaster.png"

    expected_statistics = [
        {'max': 251.0, 'checksum': 10335, 'mean': 40.872199999999999, 'stddev': 42.13926277428213, 'min': 0.0},
        {'max': 250.0, 'checksum': 9440, 'mean': 40.122500000000002, 'stddev': 40.939221948517776, 'min': 0.0},
        {'max': 252.0, 'checksum': 11907, 'mean': 42.537399999999998, 'stddev': 39.100483388827818, 'min': 0.0}
    ]


class IngestFootprintWMSRaster(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "b_id_1",
                       "bbox": ",".join(map(str, (
                            49.461072913649971,
                            -2.7625000000000002,  
                            53.079999999999998, 
                            -0.001983356685690385))),
                       "width": 100,
                       "height": 100,
                    }
                   )
    
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    
    save_to_file = "results/wms/IngestFootprintWMSRaster.png"
    
    expected_statistics = [{
        "min": 0.0,
        "max": 255.0,
        "mean": 64.406300000000002,
        "stddev": 76.223977987966478,
        "checksum": 57259
    }] * 3


class IngestRegularGridWMSRaster(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.xml"
    
    save_to_file = "results/wms/IngestRegularGridWMSRaster.png"

    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "ASAR",
                       "bbox": ",".join(map(str, 
                           (-36.259107, 16.727605000000001, -31.984922000000001, 22.301753999999999))),
                       "width": 100,
                       "height": 100,
                    }
                   )
    
    expected_statistics = [
        {'max': 251.0, 'checksum': 10783, 'mean': 29.288, 'stddev': 33.909860748755662, 'min': 0.0}
    ] * 3


class IngestFootprintCrossesDatelineRaster(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    """ Test the region until the dateline border. """
    storage_dir = "data/test_data"
    request_file = "test_data/BrowseReport_crosses_dateline.xml"
    
    save_to_file = "results/wms/IngestFootprintCrossesDatelineRaster.png"
    
    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "TEST_SAR",
                       "bbox": ",".join(map(str, (77, 170, 83, 190))),
                       "width": 100,
                       "height": 100,
                    }
                   )
    
    expected_statistics = [
        {'checksum': 22981, 'max': 250.0, 'mean': 149.01589999999999, 'min': 0.0, 'stddev': 116.91123405041111},
        {'checksum': 17526, 'max': 249.0, 'mean': 147.9785, 'min': 0.0, 'stddev': 116.12415441134544},
        {'checksum': 1612, 'max': 242.0, 'mean': 140.79480000000001, 'min': 0.0, 'stddev': 110.58494785891973}
    ]
    
class IngestFootprintCrossesDatelineRasterSecond(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    """ Test the region that overlaps the dateline boundary """
    
    storage_dir = "data/test_data"
    request_file = "test_data/BrowseReport_crosses_dateline.xml"
    
    save_to_file = "results/wms/IngestFootprintCrossesDatelineRasterSecond.png"
    
    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "TEST_SAR",
                       "bbox": ",".join(map(str, (77, -190, 83, -170))),
                       "width": 100,
                       "height": 100,
                    }
                   )
    
    expected_statistics = [
        {'checksum': 22981, 'max': 250.0, 'mean': 149.01589999999999, 'min': 0.0, 'stddev': 116.91123405041111},
        {'checksum': 17526, 'max': 249.0, 'mean': 147.9785, 'min': 0.0, 'stddev': 116.12415441134544},
        {'checksum': 1612, 'max': 242.0, 'mean': 140.79480000000001, 'min': 0.0, 'stddev': 110.58494785891973}
    ]
    
class IngestFootprintCrossesDatelineRasterThird(BaseTestCaseMixIn, HttpMixIn, StatisticsMixIn, WMSRasterMixIn, TestCase):
    """ Test the region that overlaps the dateline boundary """
    
    storage_dir = "data/test_data"
    request_file = "test_data/BrowseReport_crosses_dateline.xml"
    
    save_to_file = "results/wms/IngestFootprintCrossesDatelineRasterThird.png"
    
    wms_request = ("/ows?service=WMS&request=GetMap&version=1.3.0&"
                   "layers=%(layers)s&crs=EPSG:4326&bbox=%(bbox)s&"
                   "width=%(width)d&height=%(height)d&format=image/png" % {
                       "layers": "TEST_SAR",
                       "bbox": ",".join(map(str, (-90, -180, 90, 180))),
                       "width": 2000,
                       "height": 1000,
                    }
                   )
    
    expected_statistics = [
        {'checksum': 18991, 'max': 255.0, 'mean': 2.361958, 'min': 0.0, 'stddev': 22.611632015540938},
        {'checksum': 46269, 'max': 255.0, 'mean': 2.4702989999999998, 'min': 0.0, 'stddev': 22.501223318979772},
        {'checksum': 34188, 'max': 255.0, 'mean': 2.5279354999999999, 'min': 0.0, 'stddev': 22.22917375000339}
    ]


#===============================================================================
# Ingest command line test cases
#===============================================================================

class IngestFromCommand(IngestTestCaseMixIn, CliMixIn, TestCase):
    args = (join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_IM__0P_20100807_101327.xml"),)
    
    expected_ingested_browse_ids = ("b_id_3",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ("ASA_IM__0P_20100807_101327_proc.tif",)
    expected_deleted_files = ['ASA_IM__0P_20100807_101327.jpg']


#===============================================================================
# Delete test cases
#===============================================================================

class DeleteFromCommand(DeleteTestCaseMixIn, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    kwargs = {
        "layer" : "TEST_SAR"
    }
    
    args_before_test = ["manage.py", "ngeo_ingest_browse_report", 
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    expected_remaining_browses = 0
    expected_deleted_files = ['TEST_SAR/ASA_WS__0P_20100719_101023_proc.tif',
                              'TEST_SAR/ASA_WS__0P_20100722_101601_proc.tif',
                              'TEST_SAR/ASA_WS__0P_20100725_102231_proc.tif']
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {}

class DeleteFromCommandStart(DeleteTestCaseMixIn, CliMixIn, TestCase):
    kwargs = {
        "layer" : "TEST_SAR",
        "start": "2010-07-25T10:22Z"
    }
    
    args_before_test = ["manage.py", "ngeo_ingest_browse_report", 
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    expected_remaining_browses = 2
    expected_deleted_files = ['TEST_SAR/ASA_WS__0P_20100725_102231_proc.tif']

class DeleteFromCommandEnd(DeleteTestCaseMixIn, CliMixIn, TestCase):
    kwargs = {
        "layer" : "TEST_SAR",
        "end": "2010-07-25T10:22Z"
    }
    
    args_before_test = ["manage.py", "ngeo_ingest_browse_report", 
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    expected_remaining_browses = 1
    expected_deleted_files = ['TEST_SAR/ASA_WS__0P_20100719_101023_proc.tif',
                              'TEST_SAR/ASA_WS__0P_20100722_101601_proc.tif']

class DeleteFromCommandStartEnd(DeleteTestCaseMixIn, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    kwargs = {
        "layer" : "TEST_SAR",
        "start": "2010-07-22T10:15Z",
        "end": "2010-07-22T10:18Z"
    }
    
    args_before_test = ["manage.py", "ngeo_ingest_browse_report", 
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    expected_remaining_browses = 2
    expected_deleted_files = ['TEST_SAR/ASA_WS__0P_20100722_101601_proc.tif']
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 4, 1: 16, 2: 64, 3: 256, 4: 256}


class DeleteFromCommandStartEndMerge1(DeleteTestCaseMixIn, CliMixIn, SeedMergeTestCaseMixIn, LiveServerTestCase):
    kwargs = {
        "layer" : "TEST_SAR",
        "start": "2010-07-22T21:39:00Z",
        "end": "2010-07-22T21:40:38Z"
    }
    
    storage_dir = "data/merge_test_data"
    
    args_before_test = ["manage.py", "ngeo_ingest_browse_report", 
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_1.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_2.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_3.xml")]
    
    expected_remaining_browses = 2
    #expected_deleted_files = ['TEST_SAR/ASA_WS__0P_20100722_101601_proc.tif']
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 4, 1: 16, 2: 64, 3: 192, 4: 192}
    
    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:38:40Z"),
         parse_datetime("2010-07-22T21:39:38Z")),
        (parse_datetime("2010-07-22T21:40:38Z"),
         parse_datetime("2010-07-22T21:42:38Z"))
    ]


class DeleteFromCommandStartEndMerge2(DeleteTestCaseMixIn, CliMixIn, SeedMergeTestCaseMixIn, LiveServerTestCase):
    kwargs = {
        "layer" : "TEST_SAR",
        "start": "2010-07-22T21:39:00Z",
        "end": "2010-07-22T22:00:00Z"
    }

    storage_dir = "data/merge_test_data"

    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_1.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_2.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_3.xml")]

    expected_remaining_browses = 1
    #expected_deleted_files = ['TEST_SAR/ASA_WS__0P_20100722_101601_proc.tif']
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:38:40Z"),
         parse_datetime("2010-07-22T21:39:38Z"))
    ]


class DeleteFromCommandStartEndMerge3(DeleteTestCaseMixIn, CliMixIn, SeedMergeTestCaseMixIn, LiveServerTestCase):
    kwargs = {
        "layer" : "TEST_SAR",
        "start": "2010-07-22T21:39:01Z",
        "end": "2010-07-22T22:00:00Z"
    }

    storage_dir = "data/merge_test_data"

    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_1.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_2.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_3.xml")]

    expected_remaining_browses = 2
    #expected_deleted_files = ['TEST_SAR/ASA_WS__0P_20100722_101601_proc.tif']
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

    expected_seeded_areas = [
        (parse_datetime("2010-07-22T21:38:40Z"),
         parse_datetime("2010-07-22T21:40:38Z"))
    ]


#===============================================================================
# Export test cases
#===============================================================================

class ExportGroupFull(ExportTestCaseMixIn, CliMixIn, TestCase):
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    kwargs = {
        "layer" : "TEST_SAR"
    }
    
    expected_exported_browses = ("b_id_6", "b_id_7", "b_id_8")

class ExportGroupFullCache(ExportTestCaseMixIn, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    kwargs = {
        "layer" : "TEST_SAR"
    }
    @property
    def args(self):
        return ("--output", self.temp_export_file, "--export-cache")
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 6, 1: 24, 2: 96, 3: 384, 4: 384}
    expected_exported_browses = ("b_id_6", "b_id_7", "b_id_8")
    expected_cache_tiles = 894

class ExportGroupStart(ExportTestCaseMixIn, CliMixIn, TestCase):
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    kwargs = {
        "layer" : "TEST_SAR",
        "start": "2010-07-22T10:16:01Z"
    }
    
    expected_exported_browses = ("b_id_7", "b_id_8")

class ExportGroupEnd(ExportTestCaseMixIn, CliMixIn, TestCase):
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    kwargs = {
        "layer" : "TEST_SAR",
        "end": "2010-07-22T10:17:02Z"
    }
    
    expected_exported_browses = ("b_id_6", "b_id_7")

class ExportGroupStartEnd(ExportTestCaseMixIn, CliMixIn, TestCase):
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"),]
    
    kwargs = {
        "layer" : "TEST_SAR",
        "start": "2010-07-22T10:16:01Z",
        "end": "2010-07-22T10:17:02Z"
    }
    
    expected_exported_browses = ("b_id_7",)

class ExportRegularGrid(ExportTestCaseMixIn, CliMixIn, TestCase):
    storage_dir = "data/test_data"
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/test_data/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.xml"),]
    
    kwargs = {
        "browse-type" : "ASA_WSM"
    }
    
    expected_exported_browses = ("ASAR",)


class ExportMergedFailure(CliFailureMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    storage_dir = "data/merge_test_data"
    args_before_test = ["manage.py", "ngeo_ingest_browse_report", 
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_1.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_2.xml"),
                        join(settings.PROJECT_DIR, "data/merge_test_data/br_merge_3.xml")]
    
    command = "ngeo_export"
    kwargs = {
        "layer" : "TEST_SAR"
    }

    test_seed = None # turn off unused test
    
    @property
    def args(self):
        return ("--export-cache", )
    
    expect_failure = True
    expected_failure_msg = "Error: Browse layer 'TEST_SAR' contains merged browses and exporting of cache is requested. Try without exporting the cache.\n"


#===============================================================================
# Import test cases
#===============================================================================

class ImportIgnoreCache(ImportTestCaseMixIn, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    args = (join(settings.PROJECT_DIR, "data/export/export_SAR.tar.gz"), "--ignore-cache")
    
    expected_ingested_browse_ids = ("b_id_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ("b_id_1_proc.tif",)
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class ImportWithCache(ImportTestCaseMixIn, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    args = (join(settings.PROJECT_DIR, "data/export/export_SAR.tar.gz"),)
    
    expected_ingested_browse_ids = ("b_id_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ("b_id_1_proc.tif",)
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class ImportReplaceIgnoreCache(ImportReplaceTestCaseMixin, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"),]
    
    args = (join(settings.PROJECT_DIR, "data/export/export_SAR.tar.gz"), "--ignore-cache")
    
    expected_ingested_browse_ids = ("b_id_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_deleted_optimized_files = ("ASA_IM__0P_20100722_213840.tif",)
    expected_num_replaced = 1
    expected_optimized_files = ("b_id_1_proc.tif",)
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class ImportReplaceWithCache(ImportReplaceTestCaseMixin, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    args_before_test = ["manage.py", "ngeo_ingest_browse_report",
                        join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"),]
    
    args = (join(settings.PROJECT_DIR, "data/export/export_SAR.tar.gz"),)
    
    expected_ingested_browse_ids = ("b_id_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_deleted_optimized_files = ("ASA_IM__0P_20100722_213840.tif",)
    expected_num_replaced = 1
    expected_optimized_files = ("b_id_1_proc.tif",)
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 128, 4: 128}

class ImportRegularGrid(ImportTestCaseMixIn, CliMixIn, SeedTestCaseMixIn, LiveServerTestCase):
    args = (join(settings.PROJECT_DIR, "data/export/export_ASA_WSM.tar.gz"),)
    
    expected_ingested_browse_ids = ("ASAR",)
    expected_inserted_into_series = "TEST_ASA_WSM"
    expected_optimized_files = ("ASAR_proc.tif",)
    expected_tiles = {0: 2, 1: 8, 2: 32, 3: 64, 4: 64}


#===============================================================================
# Logging test cases
#===============================================================================

class DebugLoggingIngest(IngestTestCaseMixIn, HttpTestCaseMixin, LoggingTestCaseMixIn, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.xml"
    
    # Turn off ingest tests
    test_expected_response = None
    test_expected_status = None
    test_expected_inserted_browses = None
    test_expected_inserted_into_series = None
    test_expected_optimized_files = None
    test_model_counts = None
    test_deleted_storage_files = None
    test_expected_inserted_browses = None
    
    expected_logs = {
        logging.DEBUG: 3,
        logging.INFO: 16,
        logging.WARN: 0,
        logging.ERROR: 0,
        logging.CRITICAL: 0
    }
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': True,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'formatters': {
            'simple': {
                'format': '%(levelname)s: %(message)s'
            },
            'verbose': {
                'format': '[%(asctime)s][%(module)s] %(levelname)s: %(message)s'
            }
        },
        'handlers': {
            'ngeo_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': join(settings.PROJECT_DIR, 'logs', 'ngeo.log'),
                'formatter': 'simple',
                'filters': [],
            }
        },
        'loggers': {
            'ngeo_browse_server': {
                'handlers': ['ngeo_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
        }
    }


class InfoLoggingIngest(IngestTestCaseMixIn, HttpTestCaseMixin, LoggingTestCaseMixIn, TestCase):
    storage_dir = "data/test_data"
    request_file = "test_data/MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.xml"
    
    # Turn off ingest tests
    test_expected_response = None
    test_expected_status = None
    test_expected_inserted_browses = None
    test_expected_inserted_into_series = None
    test_expected_optimized_files = None
    test_model_counts = None
    test_deleted_storage_files = None
    test_expected_inserted_browses = None
    
    expected_logs = {
        logging.DEBUG: 0,
        logging.INFO: 16,
        logging.WARN: 0,
        logging.ERROR: 0,
        logging.CRITICAL: 0
    }
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': True,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'formatters': {
            'simple': {
                'format': '%(levelname)s: %(message)s'
            },
            'verbose': {
                'format': '[%(asctime)s][%(module)s] %(levelname)s: %(message)s'
            }
        },
        'handlers': {
            'ngeo_file': {
                'level': 'INFO',
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': join(settings.PROJECT_DIR, 'logs', 'ngeo.log'),
                'formatter': 'simple',
                'filters': [],
            }
        },
        'loggers': {
            'ngeo_browse_server': {
                'handlers': ['ngeo_file'],
                'level': 'INFO',
                'propagate': False,
            },
        }
    }


#===============================================================================
# Register test cases
#===============================================================================


class RegisterSuccess(RegisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance",
        "instanceType": "BrowseServer"
    }
    """

    expected_response = '{"result": "SUCCESS"}'
    expected_controller_config = {
        "identifier": "cs1-id",
        "address": "127.0.0.1"
    }


class RegisterFailWrongInstanceID(RegisterTestCaseMixIn, TestCase):
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "another_instance",
        "instanceType": "BrowseServer"
    }
    """

    expected_response = {
        "instanceId": "instance",
        "reason": "INSTANCE_OTHER",
        "faultString": "The provided instance ID (another_instance) is not the same as the configured one (instance)."
    }


class RegisterFailWrongControllerIP(RegisterTestCaseMixIn, TestCase):
    ip_address = "192.168.1.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance",
        "instanceType": "BrowseServer"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {
        "instanceId": "instance",
        "reason": "INTERFACE_OTHER",
        "faultString": "This browse server instance is registered on a controller server with the same ID but another IP-address ('127.0.0.1')."
    }

    test_controller_config = None


class RegisterFailWrongControllerID(RegisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs2-another-id",
        "instanceId": "instance",
        "instanceType": "BrowseServer"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {
        "instanceId": "instance",
        "reason": "ALREADY_OTHER",
        "faultString": "This browse server instance is registered on the controller server with ID 'cs1-id'."
    }

    test_controller_config = None


class RegisterFailLock(RegisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance",
        "instanceType": "BrowseServer"
    }
    """

    expected_response = {
        "instanceId": "instance",
        "reason": "ALREADY_OTHER",
        "faultString": "There is currently another registration in progress."
    }

    test_controller_config = None


    def execute(self):
        from ngeo_browse_server.lock import FileLock
        from ngeo_browse_server.control.control.config import get_controller_config_lockfile_path

        # simulate another registration process
        with FileLock(get_controller_config_lockfile_path()):
            return super(RegisterFailLock, self).execute()


class RegisterFailWrongType(RegisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance",
        "instanceType": "WebServer"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {
        "instanceId": "instance",
        "reason": "TYPE_OTHER",
        "faultString": "The provided instance type 'WebServer' is not 'BrowseServer'."
    }

    test_controller_config = None


#===============================================================================
# Unregister test cases
#===============================================================================


class UnregisterSuccessful(UnregisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {"result": "SUCCESS"}

    expected_controller_config_deleted = True



class UnregisterFailWrongInstanceID(UnregisterTestCaseMixIn, TestCase):
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "another_instance"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {
        "instanceId": "instance",
        "reason": "INSTANCE_OTHER",
        "faultString": "The provided instance ID (another_instance) is not the same as the configured one (instance)."
    }

    expected_controller_config_deleted =  False


class UnregisterFailWrongControllerIP(UnregisterTestCaseMixIn, TestCase):
    ip_address = "192.168.1.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {
        "instanceId": "instance",
        "reason": "INTERFACE_OTHER",
        "faultString": "This browse server instance is registered on a controller server with the same ID but another IP-address ('127.0.0.1')."
    }

    expected_controller_config_deleted =  False


class UnregisterFailWrongControllerID(UnregisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs2-another-id",
        "instanceId": "instance",
        "instanceType": "BrowseServer"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {
        "instanceId": "instance",
        "reason": "CONTROLLER_OTHER",
        "faultString": "This browse server instance is registered on the controller server with ID 'cs1-id'."
    }

    expected_controller_config_deleted =  False


class UnregisterFailLock(UnregisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance",
        "instanceType": "BrowseServer"
    }
    """

    controller_config = dedent("""
        [controller_server]
        identifier=cs1-id
        address=127.0.0.1
    """)

    expected_response = {
        "instanceId": "instance",
        "reason": "CONTROLLER_OTHER",
        "faultString": "There is currently another registration in progress."
    }

    expected_controller_config_deleted =  False


    def execute(self):
        from ngeo_browse_server.lock import FileLock
        from ngeo_browse_server.control.control.config import get_controller_config_lockfile_path

        # simulate another registration process
        with FileLock(get_controller_config_lockfile_path()):
            return super(UnregisterFailLock, self).execute()


class UnregisterFailUnbound(UnregisterTestCaseMixIn, TestCase):
    ip_address = "127.0.0.1"
    request = """
    {
        "controllerServerId": "cs1-id",
        "instanceId": "instance",
        "instanceType": "BrowseServer"
    }
    """

    controller_config = None # write no controller config

    expected_response = {
        "instanceId": "instance",
        "reason": "UNBOUND",
        "faultString": "This Browse Server instance was not yet registered."
    }

    expected_controller_config_deleted =  True


#===============================================================================
# Status test cases
#===============================================================================


class StatusSimple(StatusTestCaseMixIn, TestCase):
    expected_response = {
        'queues': [],
        'softwareversion': get_version(),
        'state': 'RUNNING'
    }


class StatusPaused(StatusTestCaseMixIn, TestCase):
    status_config = dedent("""
        [status]
        state=PAUSED
    """)

    expected_response = {
        'queues': [],
        'softwareversion': get_version(),
        'state': 'PAUSED'
    }


#class StatusLocked(StatusTestCaseMixIn, TestCase):
#    def execute(self):
#        from ngeo_browse_server.lock import FileLock
#        from ngeo_browse_server.control.control.config import get_controller_config_lockfile_path
#
#        # simulate another registration process
#        with FileLock(get_controller_config_lockfile_path()):
#            return super(StatusLocked, self).execute()


class ComponentControlPause(ComponentControlTestCaseMixIn, TestCase):
    command = "pause"
    expected_new_status = "PAUSED"

    expected_response = {
        "result": "SUCCESS"
    }


class ComponentControlResume(ComponentControlTestCaseMixIn, TestCase):
    command = "resume"
    expected_new_status = "RUNNING"

    status_config = dedent("""
        [status]
        state=PAUSED
    """)

    expected_response = {
        "result": "SUCCESS"
    }


class ComponentControlShutdown(ComponentControlTestCaseMixIn, TestCase):
    command = "shutdown"
    expected_new_status = "STOPPED"

    expected_response = {
        "result": "SUCCESS"
    }


class ComponentControlStart(ComponentControlTestCaseMixIn, TestCase):
    command = "start"
    expected_new_status = "RUNNING"

    status_config = dedent("""
        [status]
        state=STOPPED
    """)

    expected_response = {
        "result": "SUCCESS"
    }


class ComponentControlRestart(ComponentControlTestCaseMixIn, TestCase):
    command = "restart"
    expected_new_status = "RUNNING"

    status_config = dedent("""
        [status]
        state=STOPPED
    """)

    expected_response = {
        "result": "SUCCESS"
    }


class ComponentControlPauseFailed(ComponentControlTestCaseMixIn, TestCase):
    command = "pause"
    expected_new_status = "PAUSED"

    status_config = dedent("""
        [status]
        state=PAUSED
    """)

    expected_response = {
        'detail': {'currentState': 'PAUSED',
                   'failedState': 'pause',
                   'instanceId': 'instance'},
        'faultString': "To 'pause', the server needs to be 'running'."
    }


#===============================================================================
# Logging reporting tests
#===============================================================================


class LogListTestCase(LogListMixIn, TestCase):
    log_files = [
        ("BROW-browseServer.log", date(2013, 07, 30), "content-1"),
        ("BROW-browseServer.log-2013-07-29", date(2013, 07, 29), "content-2"),
        ("BROW-browseServer.log-2013-07-28", date(2013, 07, 28), "content-3"),
        ("BROW-eoxserver.log", date(2013, 07, 30), "content-4"),
        ("BROW-eoxserver.log-2013-07-29", date(2013, 07, 29), "content-5"),
    ]

    expected_response = {
        "dates": [{
            "date": "2013-07-30",
            "files": [
                {"name": "BROW-browseServer.log"},
                {"name": "BROW-eoxserver.log"}
            ]
        }, {
            "date": "2013-07-28",
            "files": [
                {"name": "BROW-browseServer.log-2013-07-28"}
            ]
        }, {
            "date": "2013-07-29",
            "files": [
                {"name": "BROW-browseServer.log-2013-07-29"},
                {"name": "BROW-eoxserver.log-2013-07-29"}
            ]
        }]
    }


class LogFileRetrievalTestCase(LogFileMixIn, TestCase):
    log_files = [
        ("BROW-browseServer.log", date(2013, 07, 30), "content-1"),
        ("BROW-browseServer.log-2013-07-29", date(2013, 07, 29), "content-2"),
        ("BROW-browseServer.log-2013-07-28", date(2013, 07, 28), "content-3"),
        ("BROW-eoxserver.log", date(2013, 07, 30), "content-4"),
        ("BROW-eoxserver.log-2013-07-29", date(2013, 07, 29), "content-5"),
    ]

    url = "/log/2013-07-30/BROW-browseServer.log"

    expected_response = "content-1"




class NotifyTestCase(TestCase):
    def test_notification(self):
        
        class POSTHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_len = int(self.headers.getheader('content-length'))
                post_body = self.rfile.read(content_len)
                self.send_response(200)
                self.end_headers()
                self.wfile.close()
            
            def log_request(self, *args, **kwargs):
                pass

        class ThreadedTCPServer(ThreadingMixIn, TCPServer):
            pass

        server = ThreadedTCPServer(("localhost", 9000), POSTHandler)
        server_thread = threading.Thread(target=server.serve_forever)

        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        notify("Summary", "Message", "INFO", "localhost:9000")

        server.shutdown()



class GetConfigurationAndSchemaTestCase(ConfigMixIn, TestCase):
    expected_response = """\
<getConfigurationAndSchemaResponse>
  <xsdSchema>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="ingestType">
        <xsd:sequence>
          <xsd:element type="xsd:string" name="optimized_files_postfix">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Browse file postfix</xsd:label>
                <xsd:tooltip>String that is attached at the end of filenames of optimized browses.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:string" name="compression">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Compression method</xsd:label>
                <xsd:tooltip>Compression method used. One of "JPEG", "LZW", "PACKBITS", "DEFLATE", "CCITTRLE", "CCITTFAX3", "CCITTFAX4", or "NONE". Default is "NONE"</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:integer" name="jpeg_quality">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>JPEG compression quality</xsd:label>
                <xsd:tooltip>JPEG quality if compression is "JPEG". Integer between 1-100. </xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:string" name="zlevel">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>DEFLATE Compression level</xsd:label>
                <xsd:tooltip>zlevel option for "DEFLATE" compression. Integer between 1-9.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:boolean" name="tiling">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Internal tiling</xsd:label>
                <xsd:tooltip>Defines whether or not the browse images shall be internally tiled.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:boolean" name="overviews">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Generate overviews</xsd:label>
                <xsd:tooltip>Defines whether internal browse overviews shall be generated.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:string" name="overview_resampling">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Overview resampling</xsd:label>
                <xsd:tooltip>Defines the resampling method used to generate the overviews. One of "NEAREST", "GAUSS", "CUBIC", "AVERAGE", "MODE", "AVERAGE_MAGPHASE" or "NONE".</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:string" name="overview_levels">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Overview levels</xsd:label>
                <xsd:tooltip>A comma separated list of integer overview levels. Defaults to a automatic selection of overview levels according to the dataset size.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:integer" name="overview_minsize">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Overview minimum size</xsd:label>
                <xsd:tooltip>A (positive) integer value declaring the lowest size the highest overview level at most shall have.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:boolean" name="color_index">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Color index table</xsd:label>
                <xsd:tooltip>Defines if a color index shall be calculated.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:boolean" name="footprint_alpha">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label></xsd:label>
                <xsd:tooltip>Defines whether or not a alpha channel shall be used to display the images area of interest.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:integer" name="simplification_factor">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label></xsd:label>
                <xsd:tooltip>Sets the factor for the simplification algorithm. See `http://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm` for details. Defaults to 2 (2 * resolution == 2 pixels) which provides reasonable results.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:string" name="threshold">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Merge time threshold</xsd:label>
                <xsd:tooltip>The maximum time difference between the two browse report to allow a 'merge'. E.g: 1w 5d 3h 12m 18ms. Defaults to '5h'.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
          <xsd:element type="xsd:string" name="strategy">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Ident browse strategy</xsd:label>
                <xsd:tooltip>Sets the 'strategy' for when an ingested browse is equal with an existing one. The 'merge'-strategy tries to merge the two existing images to one single. This is only possible if the time difference of the two browse reports (the report of the to be ingested browse and the one of the already existing one) is lower than the threshold. Otherwise a 'replace' is done. The 'replace' strategy removes the previous browse, before ingesting the new one.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="cacheType">
        <xsd:sequence>
          <xsd:element type="xsd:integer" name="threads">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label></xsd:label>
                <xsd:tooltip></xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="logType">
        <xsd:sequence>
          <xsd:element type="levelType" name="level">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Log level</xsd:label>
                <xsd:tooltip>Log level, to determine which log types shall be logged.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="webServerType">
        <xsd:sequence>
          <xsd:element type="xsd:string" name="baseurl">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:label>Web Server base URL</xsd:label>
                <xsd:tooltip>Base URL of the ngEO Web Server for authorization requests.</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:element>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:simpleType name="levelType">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="DEBUG">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:tooltip>Log debug, info, warning and error messages</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:enumeration>
          <xsd:enumeration value="INFO">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:tooltip>Log info, warning and error messages</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:enumeration>
          <xsd:enumeration value="WARNING">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:tooltip>Log warning and error messages</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:enumeration>
          <xsd:enumeration value="ERROR">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:tooltip>Log only error messages</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:enumeration>
          <xsd:enumeration value="OFF">
            <xsd:annotation>
              <xsd:documentation>
                <xsd:tooltip>Turn logging off</xsd:tooltip>
              </xsd:documentation>
            </xsd:annotation>
          </xsd:enumeration>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:complexType name="configurationType">
        <xsd:sequence>
          <xsd:element type="ingestType" name="ingest"/>
          <xsd:element type="cacheType" name="cache"/>
          <xsd:element type="logType" name="log"/>
          <xsd:element type="webServerType" name="webServer"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element type="configurationType" name="configuration"/>
    </xsd:schema>
  </xsdSchema>
  <configurationData>
    <configuration>
      <ingest>
        <optimized_files_postfix>_proc</optimized_files_postfix>
        <compression>LZW</compression>
        <jpeg_quality>75</jpeg_quality>
        <zlevel>6</zlevel>
        <tiling>true</tiling>
        <overviews>true</overviews>
        <overview_resampling>NEAREST</overview_resampling>
        <overview_levels>2,4,8,16</overview_levels>
        <overview_minsize>256</overview_minsize>
        <color_index>false</color_index>
        <footprint_alpha>true</footprint_alpha>
        <simplification_factor>2</simplification_factor>
        <threshold>5h</threshold>
        <strategy>merge</strategy>
      </ingest>
      <cache>
        <threads>1</threads>
      </cache>
      <log>
        <level>INFO</level>
      </log>
      <webServer>
        <baseurl>http://www.example.com/</baseurl>
      </webServer>
    </configuration>
  </configurationData>
</getConfigurationAndSchemaResponse>
"""

class AddBrowseLayerTestCase(ConfigurationManagementMixIn, TestCase):
    # operating on an "empty" server.
    fixtures = ["initial_rangetypes.json",]

    expected_layers = ["TEST_SAR"]

    request = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<synchronizeConfiguration xmlns="http://ngeo.eo.esa.int/schema/configurationElements">
  <startRevision>0</startRevision>
  <endRevision>1</endRevision>
  <removeConfiguration />
  <addConfiguration>
    <browseLayers>
      <browseLayer browseLayerId="TEST_SAR">
        <browseType>SAR</browseType>
        <title>TEST_SAR</title>
        <description>TEST_SAR Browse Layer</description>
        <browseAccessPolicy>OPEN</browseAccessPolicy>
        <hostingBrowseServerName>browse_GMV</hostingBrowseServerName>
        <relatedDatasetIds>
          <datasetId>ENVISAT_ASA_WS__0P</datasetId>
        </relatedDatasetIds>
        <containsVerticalCurtains>false</containsVerticalCurtains>
        <rgbBands>1,2,3</rgbBands>
        <grid>urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible</grid>
        <radiometricInterval>
          <min>0</min>
          <max>6</max>
        </radiometricInterval>
        <highestMapLevel>6</highestMapLevel>
        <lowestMapLevel>0</lowestMapLevel>
        <tileQueryLimit>100</tileQueryLimit>
        <timeDimensionDefault>2010</timeDimensionDefault>
      </browseLayer>
    </browseLayers>
  </addConfiguration>
</synchronizeConfiguration>
"""

    expected_response = '<?xml version="1.0"?>\n<synchronizeConfigurationResponse>1</synchronizeConfigurationResponse>'


class AddBrowseLayerDefaultTileAndTimeTestCase(ConfigurationManagementMixIn, TestCase):
    # operating on an "empty" server.
    fixtures = ["initial_rangetypes.json",]

    expected_layers = ["TEST_SAR"]

    configuration = {
        ("mapcache", "timedimension_default"): "2015",
        ("mapcache", "tile_query_limit_default"): "75"
    }

    request = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<synchronizeConfiguration xmlns="http://ngeo.eo.esa.int/schema/configurationElements">
  <startRevision>0</startRevision>
  <endRevision>1</endRevision>
  <removeConfiguration />
  <addConfiguration>
    <browseLayers>
      <browseLayer browseLayerId="TEST_SAR">
        <browseType>SAR</browseType>
        <title>TEST_SAR</title>
        <description>TEST_SAR Browse Layer</description>
        <browseAccessPolicy>OPEN</browseAccessPolicy>
        <hostingBrowseServerName>browse_GMV</hostingBrowseServerName>
        <relatedDatasetIds>
          <datasetId>ENVISAT_ASA_WS__0P</datasetId>
        </relatedDatasetIds>
        <containsVerticalCurtains>false</containsVerticalCurtains>
        <rgbBands>1,2,3</rgbBands>
        <grid>urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible</grid>
        <radiometricInterval>
          <min>0</min>
          <max>6</max>
        </radiometricInterval>
        <highestMapLevel>6</highestMapLevel>
        <lowestMapLevel>0</lowestMapLevel>
      </browseLayer>
    </browseLayers>
  </addConfiguration>
</synchronizeConfiguration>
"""

    expected_response = '<?xml version="1.0"?>\n<synchronizeConfigurationResponse>1</synchronizeConfigurationResponse>'

    def test_tile_and_time(self):
        browse_layer_model = models.BrowseLayer.objects.get(id="TEST_SAR")
        self.assertEqual(browse_layer_model.tile_query_limit, 75)
        self.assertEqual(browse_layer_model.timedimension_default, "2015")


class AddBrowseLayerDefaultTileAndTimeDefaultTestCase(ConfigurationManagementMixIn, TestCase):
    # operating on an "empty" server.
    fixtures = ["initial_rangetypes.json",]

    expected_layers = ["TEST_SAR"]

    request = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<synchronizeConfiguration xmlns="http://ngeo.eo.esa.int/schema/configurationElements">
  <startRevision>0</startRevision>
  <endRevision>1</endRevision>
  <removeConfiguration />
  <addConfiguration>
    <browseLayers>
      <browseLayer browseLayerId="TEST_SAR">
        <browseType>SAR</browseType>
        <title>TEST_SAR</title>
        <description>TEST_SAR Browse Layer</description>
        <browseAccessPolicy>OPEN</browseAccessPolicy>
        <hostingBrowseServerName>browse_GMV</hostingBrowseServerName>
        <relatedDatasetIds>
          <datasetId>ENVISAT_ASA_WS__0P</datasetId>
        </relatedDatasetIds>
        <containsVerticalCurtains>false</containsVerticalCurtains>
        <rgbBands>1,2,3</rgbBands>
        <grid>urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible</grid>
        <radiometricInterval>
          <min>0</min>
          <max>6</max>
        </radiometricInterval>
        <highestMapLevel>6</highestMapLevel>
        <lowestMapLevel>0</lowestMapLevel>
      </browseLayer>
    </browseLayers>
  </addConfiguration>
</synchronizeConfiguration>
"""

    expected_response = '<?xml version="1.0"?>\n<synchronizeConfigurationResponse>1</synchronizeConfigurationResponse>'

    def test_tile_and_time(self):
        browse_layer_model = models.BrowseLayer.objects.get(id="TEST_SAR")
        self.assertEqual(browse_layer_model.tile_query_limit, 100)
        self.assertEqual(browse_layer_model.timedimension_default, "2014")


class AddDefaultBrowseLayersTestCase(ConfigurationManagementMixIn, TestCase):
    # operating on an "empty" server.
    fixtures = ["initial_rangetypes.json",]

    expected_layers = [
        "TEST_SAR", "TEST_OPTICAL", "TEST_ASA_WSM", "TEST_MER_FRS", 
        "TEST_MER_FRS_FULL", "TEST_MER_FRS_FULL_NO_BANDS", 
        "TEST_GOOGLE_MERCATOR"
    ]

    request_file = "layer_management/synchronizeConfiguration_defaultLayers.xml"

    expected_response = '<?xml version="1.0"?>\n<synchronizeConfigurationResponse>2</synchronizeConfigurationResponse>'


class RemoveBrowseLayerTestCase(ConfigurationManagementMixIn, TestCase):
    expected_removed_layers = ["TEST_SAR"]

    request = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<synchronizeConfiguration xmlns="http://ngeo.eo.esa.int/schema/configurationElements">
  <startRevision>0</startRevision>
  <endRevision>1</endRevision>
  <addConfiguration />
  <removeConfiguration>
    <browseLayers>
      <browseLayer browseLayerId="TEST_SAR">
        <browseType>SAR</browseType>
        <title>TEST_SAR</title>
        <description>TEST_SAR Browse Layer</description>
        <browseAccessPolicy>OPEN</browseAccessPolicy>
        <hostingBrowseServerName>browse_GMV</hostingBrowseServerName>
        <relatedDatasetIds>
          <datasetId>ENVISAT_ASA_WS__0P</datasetId>
        </relatedDatasetIds>
        <containsVerticalCurtains>false</containsVerticalCurtains>
        <rgbBands>1,2,3</rgbBands>
        <grid>urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible</grid>
        <radiometricInterval>
          <min>0</min>
          <max>6</max>
        </radiometricInterval>
        <highestMapLevel>6</highestMapLevel>
        <lowestMapLevel>0</lowestMapLevel>
        <tileQueryLimit>100</tileQueryLimit>
        <timeDimensionDefault>2010</timeDimensionDefault>
      </browseLayer>
    </browseLayers>
  </removeConfiguration>
</synchronizeConfiguration>
"""

    expected_response = '<?xml version="1.0"?>\n<synchronizeConfigurationResponse>1</synchronizeConfigurationResponse>'

#===============================================================================
# Report generation command line test cases
#===============================================================================

class ReportAccessTestCase(GenerateReportMixIn, TestCase):
    access_logfile = join(settings.PROJECT_DIR, "data/report_logs/access.log")

    expected_report = """\
<fetchReportDataResponse>
  <report>
    <header>
      <operation>BROWSE_ACCESS</operation>
      <component>instance</component>
      <date>2014-04-07T13:00:08Z</date>
    </header>
    <data>
      <value key="browselayers">layerA</value>
      <value key="userid">-</value>
      <value key="numRequests">1</value>
      <value key="aggregatedSize">1576</value>
      <value key="aggregatedProcessingTime">2500</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_ACCESS</operation>
      <component>instance</component>
      <date>2014-04-12T13:00:08Z</date>
    </header>
    <data>
      <value key="browselayers">layerB</value>
      <value key="userid">-</value>
      <value key="numRequests">5</value>
      <value key="aggregatedSize">7880</value>
      <value key="aggregatedProcessingTime">9907</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_ACCESS</operation>
      <component>instance</component>
      <date>2014-04-13T13:00:08Z</date>
    </header>
    <data>
      <value key="browselayers">layerA,layerB</value>
      <value key="userid">-</value>
      <value key="numRequests">1</value>
      <value key="aggregatedSize">1576</value>
      <value key="aggregatedProcessingTime">1956</value>
    </data>
  </report>
</fetchReportDataResponse>
"""


class ReportAccessSubsetTestCase(GenerateReportMixIn, TestCase):
    access_logfile = join(settings.PROJECT_DIR, "data/report_logs/access.log")
    begin = "2014-04-08T15:31:15Z" 
    end = "2014-04-10T20:30Z"

    expected_report = """\
<fetchReportDataResponse>
  <report>
    <header>
      <operation>BROWSE_ACCESS</operation>
      <component>instance</component>
      <date>2014-04-10T13:00:08Z</date>
    </header>
    <data>
      <value key="browselayers">layerB</value>
      <value key="userid">-</value>
      <value key="numRequests">2</value>
      <value key="aggregatedSize">3152</value>
      <value key="aggregatedProcessingTime">2406</value>
    </data>
  </report>
</fetchReportDataResponse>
"""


class ReportIngestTestCase(GenerateReportMixIn, TestCase):
    report_logfile = join(settings.PROJECT_DIR, "data/report_logs/ingest.log")

    expected_report = """\
<fetchReportDataResponse>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-07T15:30:33Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">1</value>
      <value key="numberOfSuccessfulBrowses">0</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-08T15:31:15Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-09T15:31:42Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-10T15:31:47Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T10:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-11T15:31:48Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">1</value>
      <value key="numberOfSuccessfulBrowses">0</value>
      <value key="dateTime">2012-11-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-12T15:31:51Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-13T15:31:54Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
</fetchReportDataResponse>
"""

class ReportIngestSubsetTestCase(GenerateReportMixIn, TestCase):
    report_logfile = join(settings.PROJECT_DIR, "data/report_logs/ingest.log")
    begin="2014-04-08T15:31:15Z"
    end="2014-04-10T20:30Z"

    expected_report = """\
<fetchReportDataResponse>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-08T15:31:15Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-09T15:31:42Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-10T15:31:47Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T10:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
</fetchReportDataResponse>
"""

class ReportBothSubsetTestCase(GenerateReportMixIn, TestCase):
    report_logfile = join(settings.PROJECT_DIR, "data/report_logs/ingest.log")
    access_logfile = join(settings.PROJECT_DIR, "data/report_logs/access.log")
    begin = "2014-04-08T15:31:15Z"
    end = "2014-04-10T20:30Z"

    expected_report = """\
<fetchReportDataResponse>
  <report>
    <header>
      <operation>BROWSE_ACCESS</operation>
      <component>instance</component>
      <date>2014-04-10T13:00:08Z</date>
    </header>
    <data>
      <value key="browselayers">layerB</value>
      <value key="userid">-</value>
      <value key="numRequests">2</value>
      <value key="aggregatedSize">3152</value>
      <value key="aggregatedProcessingTime">2406</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-08T15:31:15Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-09T15:31:42Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T09:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
  <report>
    <header>
      <operation>BROWSE_REPORT</operation>
      <component>instance</component>
      <date>2014-04-10T15:31:47Z</date>
    </header>
    <data>
      <value key="browseType">SAR</value>
      <value key="numberOfFailedBrowses">0</value>
      <value key="numberOfSuccessfulBrowses">1</value>
      <value key="dateTime">2012-10-02T10:30:00+00:00</value>
      <value key="numberOfContainedBrowses">1</value>
      <value key="responsibleOrgName">ESA</value>
    </data>
  </report>
</fetchReportDataResponse>
"""
