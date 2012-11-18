#!/bin/sh
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

# About:
# =====
# This script loads demo data in an ngEO Browse Server instance.

# Running:
# =======
# sudo ./load_demo_in_ngeo_browse_server.sh

################################################################################
# Adjust the variables to your liking.                                         #
################################################################################

# ngEO Browse Server
NGEOB_INSTALL_DIR="/var/www/ngeo"

# MapCache
MAPCACHE_DIR="/var/www/cache"

################################################################################
# Usually there should be no need to change anything below.                    #
################################################################################

echo "==============================================================="
echo "load_demo_in_ngeo_browse_server.sh"
echo "==============================================================="

echo "Started loading demo data"

# ngEO Browse Server
cd "$NGEOB_INSTALL_DIR"
    
    # TODO download demo data
    python manage.py loaddata auth_data.json ngeo_browse_layer.json eoxs_dataset_series.json
    python manage.py loaddata --database=mapcache ngeo_mapcache.json
    python manage.py ngeo_ingest_browse_report /home/meissls/reference_test_data/*.xml --storage-dir=/home/meissls/reference_test_data/


# MapCache
cd "$MAPCACHE_DIR"

    #TODO mapcache.xml
    mapcache_seed -t TEST_SAR -v -z 0,7 -p 4 -c mapcache.xml
    mapcache_seed -t TEST_OPTICAL -v -z 0,7 -p 4 -c mapcache.xml

    # Make the cache read- and editable by apache
    chown -R apache:apache .

echo "Finished loading demo data"
