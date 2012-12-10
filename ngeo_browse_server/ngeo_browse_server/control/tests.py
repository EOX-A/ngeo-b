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
from django.test import TestCase, LiveServerTestCase

from ngeo_browse_server.control.testbase import (
    BaseTestCaseMixIn, HttpMixIn, CliMixIn, IngestTestCaseMixIn,
    IngestReplaceTestCaseMixIn, OverviewMixIn, CompressionMixIn, BandCountMixIn,
    HasColorTableMixIn, ExtentMixIn, SizeMixIn, ProjectionMixIn,
    IngestFailureTestCaseMixIn
)
from ngeo_browse_server.control.ingest.config import (
    INGEST_SECTION, MAPCACHE_SECTION
)


#===============================================================================
# Ingest ModelInGeoTiff test case
#===============================================================================

class IngestModelInGeotiffBrowse(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data"
    
    expected_ingested_browse_ids = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_proc.tif']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced</rep:browseIdentifier>
        <rep:fileName>mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.tif</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:modelInGeotiff>true</rep:modelInGeotiff>
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
            <bsi:identifier>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


#===============================================================================
# Ingest Rectified browse test case
#===============================================================================

class IngestRectifiedBrowse(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data"
    
    expected_ingested_browse_ids = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced_proc.tif']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>OPTICAL</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced</rep:browseIdentifier>
        <rep:fileName>mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.tif</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:rectifiedBrowse>
            <rep:coordList>32.1902500 8.4784500 46.2686450 25.4101500</rep:coordList>
        </rep:rectifiedBrowse>
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
            <bsi:identifier>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""


#===============================================================================
# Ingest Regular Grid test case
#===============================================================================

class IngestRegularGridBrowse(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    storage_dir = "data"
    
    expected_ingested_browse_ids = ("ASAR",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775_proc.tif']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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
    
class IngestFootprintBrowse(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100722_213840.xml"
    
    expected_ingested_browse_ids = ("b_id_1",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100722_213840_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100722_213840.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestFootprintBrowse2(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100731_103315.xml"
    
    expected_ingested_browse_ids = ("b_id_2",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100731_103315_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100731_103315.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestFootprintBrowse3(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100813_102453.xml"
    
    expected_ingested_browse_ids = ("b_id_5",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100813_102453_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100813_102453.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestFootprintBrowse4(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100719_105257.xml"
    
    expected_ingested_browse_ids = ("b_id_9",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100719_105257_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100719_105257.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestFootprintBrowse5(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100719_213253.xml"
    
    expected_ingested_browse_ids = ("b_id_10",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100719_213253_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100719_213253.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestFootprintBrowse6(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ATS_TOA_1P_20100722_101606.xml"
    
    expected_ingested_browse_ids = ("b_id_11",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100722_101606_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100722_101606.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestBrowseNoID(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    
    expected_ingested_browse_ids = (None,)
    expected_ingested_coverage_ids = ("TEST_OPTICAL_20100722101606000000_20100722101722000000",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100722_101606_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100722_101606.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestBrowseSpecialID(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    
    expected_ingested_browse_ids = ("some:special:id",)
    expected_ingested_coverage_ids = ("TEST_OPTICAL_20100722101606000000_20100722101722000000",)
    expected_inserted_into_series = "TEST_OPTICAL"
    expected_optimized_files = ['ATS_TOA_1P_20100722_101606_proc.tif']
    expected_deleted_files = ['ATS_TOA_1P_20100722_101606.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 16, 7: 24, 8: 48}
    
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

class IngestFootprintBrowseGroup(IngestTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    request_file = "reference_test_data/browseReport_ASA_WS__0P_20100719_101023_group.xml"
    
    expected_ingested_browse_ids = ("b_id_6", "b_id_7", "b_id_8")
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_WS__0P_20100719_101023_proc.tif',
                                'ASA_WS__0P_20100722_101601_proc.tif',
                                'ASA_WS__0P_20100725_102231_proc.tif']
    expected_deleted_files = ['ASA_WS__0P_20100719_101023.jpg',
                              'ASA_WS__0P_20100722_101601.jpg',
                              'ASA_WS__0P_20100725_102231.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 36, 7: 76, 8: 196}

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

class IngestFootprintBrowseReplace(IngestReplaceTestCaseMixIn, HttpMixIn, LiveServerTestCase):
    fixtures = IngestReplaceTestCaseMixIn.fixtures + ["browse_ASA_IM__0P_20100807_101327.json"]
    request_file = "reference_test_data/browseReport_ASA_IM__0P_20100807_101327_new.xml"
    
    expected_num_replaced = 1
    
    expected_ingested_browse_ids = ("b_id_3",)
    expected_inserted_into_series = "TEST_SAR"
    expected_optimized_files = ['ASA_IM__0P_20100807_101327_new_proc.tif']
    expected_deleted_files = ['ASA_IM__0P_20100807_101327_new.jpg']
    expected_tiles = {0: 2, 1: 8, 2: 8, 3: 8, 4: 8, 5: 16, 6: 36, 7: 76, 8: 196}
    
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
    expected_generated_failure_browse_report = "SAR_EOX_20121002093000000000.xml"

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


class IngestFailureIDStartsWithNumber(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("11_id_starts_with_number",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000.xml"
    
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


class IngestFailureFootprintNoCircle(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000.xml"
    
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
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000.xml"
    
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
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000.xml"
    
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


class IngestFailureFileOverwrite(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    """ Test to check that the program fails when a file in the optimized files
        dir would be overwritten.
    """
    
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000.xml"
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


class IngestFailureNoMapCache(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expected_failed_browse_ids = ("FAILURE",)
    expected_failed_files = ["ATS_TOA_1P_20100722_101606.jpg"]
    expected_generated_failure_browse_report = "OPTICAL_ESA_20121002093000000000.xml"
    
    configuration = {
        (MAPCACHE_SECTION, "seed_command"): "/dev/null"
    }
    
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
                <bsi:exceptionCode>OSError</bsi:exceptionCode>
                <bsi:exceptionMessage>[Errno 13] Permission denied</bsi:exceptionMessage>
            </bsi:error>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""

class IngestFailureInvalidXML(IngestFailureTestCaseMixIn, HttpMixIn, TestCase):
    expect_exception = True
    
    request = ""

    expected_response = """\
<bsi:ingestException xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:exceptionCode>InvalidRequest</bsi:exceptionCode>
    <bsi:exceptionMessage>Could not parse request XML. Error was: &#39;Start tag expected, &#39;&lt;&#39; not found, line 1, column 1&#39;.</bsi:exceptionMessage>
</bsi:ingestException>
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
