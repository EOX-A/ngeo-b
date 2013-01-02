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
    ExtentMixIn, SizeMixIn, ProjectionMixIn, IngestFailureTestCaseMixIn
)
from ngeo_browse_server.control.ingest.config import (
    INGEST_SECTION, MAPCACHE_SECTION
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
    expected_tiles = {0: 2, 1: 4, 2: 4, 3: 16, 4: 16, 5: 36, 6: 80, 7: 168, 8: 624}


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
    expected_tiles = {0: 2, 1: 4, 2: 4, 3: 16, 4: 16, 5: 36, 6: 80, 7: 168, 8: 624}


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
    expected_tiles = {0: 2, 1: 4, 2: 8, 3: 4, 4: 16, 5: 16, 6: 24, 7: 48, 8: 96}

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
    expected_tiles = {0: 2, 1: 4, 2: 4, 3: 8, 4: 8, 5: 8, 6: 8, 7: 16, 8: 16}


#===============================================================================
# Ingest Footprint browse test cases
#===============================================================================
    
class IngestFootprintBrowse(IngestTestCaseMixIn, HttpTestCaseMixin, TestCase):
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

class SeedFootprintBrowse(SeedTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    
    expected_inserted_into_series = "TEST_SAR"
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}

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
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 16, 8: 36}

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
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 36, 8: 36}

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
    expected_tiles = {0: 2, 1: 4, 2: 4, 3: 4, 4: 8, 5: 4, 6: 16, 7: 8, 8: 4}


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
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 36, 7: 60, 8: 216}

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
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 36, 7: 60, 8: 160}

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
    expected_tiles = {0: 2, 1: 4, 2: 4, 3: 4, 4: 4, 5: 16, 6: 24, 7: 80, 8: 168}


#===============================================================================
# Arbitrary ingests
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
    expected_tiles = {0: 2, 1: 4, 2: 4, 3: 4, 4: 4, 5: 16, 6: 24, 7: 80, 8: 168}

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
    expected_tiles = {0: 2, 1: 4, 2: 4, 3: 4, 4: 4, 5: 16, 6: 24, 7: 80, 8: 168}

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
    expected_tiles = {0: 6, 1: 24, 2: 24, 3: 24, 4: 24, 5: 48, 6: 76, 7: 144, 8: 348}

#===============================================================================
# Ingest a browse report which includes a replacement of a previous browse
#===============================================================================

class IngestFootprintBrowseReplace(IngestReplaceTestCaseMixIn, HttpTestCaseMixin, TestCase):
    request_before_replace_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327.xml"
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
    expected_tiles = {0: 4, 1: 16, 2: 16, 3: 16, 4: 16, 5: 32, 6: 40, 7: 96, 8: 236}


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
                <bsi:exceptionCode>RuntimeError</bsi:exceptionCode>
                <bsi:exceptionMessage>EPSG PCS/GCS code 999999 not found in EPSG support files.  Is this a valid
EPSG coordinate system?</bsi:exceptionMessage>
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
    
    copy_to_optimized = [("reference_test_data/ATS_TOA_1P_20100722_101606.jpg", "TEST_OPTICAL/ATS_TOA_1P_20100722_101606_proc.tif")]
    
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
                <bsi:exceptionMessage>Output file &#39;%s/TEST_OPTICAL/ATS_TOA_1P_20100722_101606_proc.tif&#39; already exists.</bsi:exceptionMessage>
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


#===============================================================================
# Raster test cases
#===============================================================================

    
class IngestRasterOverviewsAutomatic(BaseTestCaseMixIn, HttpMixIn, OverviewMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "overviews"): "true",
        (INGEST_SECTION, "overview_minsize"): "100"
    }
    
    expected_overview_count = 4
    

class IngestRasterOverviewsFixed(BaseTestCaseMixIn, HttpMixIn, OverviewMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "overviews"): "true",
        (INGEST_SECTION, "overview_levels"): "2,4"
    }
    
    expected_overview_count = 2


class IngestRasterNoOverviews(BaseTestCaseMixIn, HttpMixIn, OverviewMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "overviews"): "false"
    }
    
    expected_overview_count = 0

        
class IngestRasterCompression(BaseTestCaseMixIn, HttpMixIn, CompressionMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "compression"): "DEFLATE"
    }
    
    expected_compression = "DEFLATE"


class IngestRasterNoCompression(BaseTestCaseMixIn, HttpMixIn, CompressionMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "compression"): "NONE"
    }
    
    expected_compression = None


class IngestRasterFootprintAlpha(BaseTestCaseMixIn, HttpMixIn, BandCountMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "footprint_alpha"): "true"
    }
    
    expected_band_count = 4


class IngestRasterNoFootprintAlpha(BaseTestCaseMixIn, HttpMixIn, BandCountMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "footprint_alpha"): None
    }
    
    expected_band_count = 3


class IngestRasterColorIndex(BaseTestCaseMixIn, HttpMixIn, HasColorTableMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    configuration = {
        (INGEST_SECTION, "color_index"): "true",
        (INGEST_SECTION, "footprint_alpha"): "false",
    }


class IngestRasterExtent(BaseTestCaseMixIn, HttpMixIn, ExtentMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    expected_extent = (-2.774285714285714, 
                       49.459259284618561, 
                       0.0023992109516033366, 
                       53.079999999999991)


class IngestRasterSize(BaseTestCaseMixIn, HttpMixIn, SizeMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    expected_size = (1181, 1540)


class IngestRasterProjectionEPSG4326(BaseTestCaseMixIn, HttpMixIn, ProjectionMixIn, TestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    raster_file = property(lambda self: join(self.temp_optimized_files_dir, "TEST_SAR", "ASA_IM__0P_20100722_213840_proc.tif"))
    
    expected_projection_srid = 4326


#===============================================================================
# Command line ingestion test cases
#===============================================================================

class IngestFromCommand(IngestTestCaseMixIn, CliMixIn, TestCase):
    args = (join(settings.PROJECT_DIR, "data/reference_test_data/browseReport_ASA_IM__0P_20100807_101327.xml"),)
    
    expected_ingested_browse_ids = ("b_id_3",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ("ASA_IM__0P_20100807_101327_proc.tif",)
    expected_deleted_files = ['ASA_IM__0P_20100807_101327.jpg']
