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

from django.conf import settings
from django.test import TestCase, TransactionTestCase, LiveServerTestCase

from ngeo_browse_server.control.testbase import (
    BaseTestCaseMixIn, HttpTestCaseMixin, HttpMixIn, CliMixIn, 
    IngestTestCaseMixIn, SeedTestCaseMixIn, IngestReplaceTestCaseMixIn, 
    OverviewMixIn, CompressionMixIn, BandCountMixIn, HasColorTableMixIn, 
    ExtentMixIn, SizeMixIn, ProjectionMixIn, StatisticsMixIn, WMSRasterMixIn,
    IngestFailureTestCaseMixIn, DeleteTestCaseMixIn, ExportTestCaseMixIn,
    ImportTestCaseMixIn, ImportReplaceTestCaseMixin
)
from ngeo_browse_server.control.ingest.config import (
    INGEST_SECTION
)

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
                <bsi:exceptionMessage>{&#39;value&#39;: [u&#39;This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops.&#39;]}</bsi:exceptionMessage>
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
                <bsi:exceptionMessage>{&#39;value&#39;: [u&#39;This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops.&#39;]}</bsi:exceptionMessage>
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


class IngestFailureFileOverwrite(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    """ Test to check that the program fails when a file in the optimized files
        dir would be overwritten.
    """
    
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000_(.*).xml"
    expected_optimized_files = ["ATS_TOA_1P_20100722_101606_proc.tif"]
    
    copy_to_optimized = [("reference_test_data/ATS_TOA_1P_20100722_101606.jpg", "TEST_OPTICAL/2010/ATS_TOA_1P_20100722_101606_proc.tif")]
    
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
        <rep:endTime>2010-07-22T10:17:22Z</rep:endTime>
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
                <bsi:exceptionMessage>Output file &#39;%s/TEST_OPTICAL/2010/ATS_TOA_1P_20100722_101606_proc.tif&#39; already exists and is not to be replaced.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
""" % self.temp_optimized_files_dir


class IngestFailureInvalidXML(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
    expect_exception = True
    
    request = ""

    expected_response = """\
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Could not parse request XML. Error was: &#39;Start tag expected, &#39;&lt;&#39; not found, line 1, column 1&#39;.</bsi:exceptionMessage>
</bsi:ingestException>
"""


class IngestFailureGCPTransformException(IngestFailureTestCaseMixIn, HttpTestCaseMixin, TestCase):
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
                <bsi:exceptionCode>GCPTransformException</bsi:exceptionCode>
                <bsi:exceptionMessage>Could not find a valid transform method.</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
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
                       49.46107291365005, 
                       -0.029483356685753748, 
                       53.079999999999991)


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
        "mean": 64.244023630714196,
        "stddev": 76.138905033891447,
        "checksum": 13096
    }, {
        "min": 0.0,
        "max": 255.0,
        "mean": 64.244023630714196,
        "stddev": 76.138905033891447,
        "checksum": 13096
    }, {
        "min": 0.0,
        "max": 255.0,
        "mean": 64.244023630714196,
        "stddev": 76.138905033891447,
        "checksum": 13096
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
        "mean": 64.370999999999995,
        "stddev": 76.192750042244839,
        "checksum": 57389
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
        {'max': 251.0, 'checksum': 11342, 'mean': 29.2577, 'stddev': 33.854823743596718, 'min': 0.0}
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
        {'checksum': 22934, 'max': 250.0, 'mean': 148.99510000000001, 'min': 0.0, 'stddev': 116.90873567013715},
        {'checksum': 17599, 'max': 249.0, 'mean': 147.95439999999999, 'min': 0.0, 'stddev': 116.12004013364789},
        {'checksum': 1606, 'max': 242.0, 'mean': 140.77260000000001, 'min': 0.0, 'stddev': 110.5817764789479}
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
    
    # TODO: this does not yet work. Replace this to something useful once the test finishes
    expected_statistics = [{'checksum': 22934, 'max': 250.0, 'mean': 148.99510000000001, 'min': 0.0, 'stddev': 116.90873567013715},
                           {'checksum': 17599, 'max': 249.0, 'mean': 147.95439999999999, 'min': 0.0, 'stddev': 116.12004013364789},
                           {'checksum': 1606, 'max': 242.0, 'mean': 140.77260000000001, 'min': 0.0, 'stddev': 110.5817764789479}]
    
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
    
    # TODO: this does not yet work. Replace this to something useful once the test finishes
    expected_statistics = [{'checksum': 19103, 'max': 255.0, 'mean': 2.3617534999999998, 'min': 0.0, 'stddev': 22.610579181109841},
                           {'checksum': 46676, 'max': 255.0, 'mean': 2.4700384999999998, 'min': 0.0, 'stddev': 22.499895873281673},
                           {'checksum': 34584, 'max': 255.0, 'mean': 2.527612, 'min': 0.0, 'stddev': 22.227140899752627}]


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
