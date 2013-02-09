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
# This script resets the autotest instance used in testing via vagrant.
#
# Use with caution as data is deleted and may be lost.
# Particularly only use in testing and never in production environments.

# Running:
# =======
# ./reset_db.sh
# Passwords is vagrant
#
################################################################################

sudo service httpd stop

# Reset DB with PostgreSQL:
dropdb ngeo
rm -f /var/ngeob_data/mapcache.sqlite
createdb -O vagrant -T template_postgis ngeo
cd /var/ngeob/
python manage.py syncdb --noinput
python manage.py syncdb --database=mapcache --noinput
python manage.py loaddata auth_data.json ngeo_browse_layer.json eoxs_dataset_series.json initial_rangetypes.json
python manage.py loaddata --database=mapcache ngeo_mapcache.json
sudo chown apache:apache /var/ngeob_data/mapcache.sqlite
sudo chmod a+w /var/ngeob_data/mapcache.sqlite

## Reset DB with Django:
## Note, schema changes are not applied.
#cd /var/ngeob/
#python manage.py flush
#python manage.py flush --database=mapcache
#python manage.py loaddata auth_data.json ngeo_browse_layer.json eoxs_dataset_series.json initial_rangetypes.json
#python manage.py loaddata --database=mapcache ngeo_mapcache.json

# Reset ngEO Browse Server
sudo rm -rf /var/ngeob_data/optimized/TEST_*
sudo rm -rf /var/ngeob_data/success/*
sudo rm -rf /var/ngeob_data/failure/*
rm -f /var/ngeob/autotest/logs/eoxserver.log /var/ngeob/autotest/logs/ngeo.log
touch /var/ngeob/autotest/logs/eoxserver.log /var/ngeob/autotest/logs/ngeo.log
chmod go+w /var/ngeob/autotest/logs/eoxserver.log /var/ngeob/autotest/logs/ngeo.log

# Reset MapCache
rm -f /var/www/cache/TEST_SAR.sqlite /var/www/cache/TEST_OPTICAL.sqlite /var/www/cache/TEST_ASA_WSM.sqlite /var/www/cache/TEST_MER_FRS.sqlite
touch /var/www/cache/TEST_SAR.sqlite /var/www/cache/TEST_OPTICAL.sqlite /var/www/cache/TEST_ASA_WSM.sqlite /var/www/cache/TEST_MER_FRS.sqlite
chmod go+w /var/www/cache/TEST_SAR.sqlite /var/www/cache/TEST_OPTICAL.sqlite /var/www/cache/TEST_ASA_WSM.sqlite /var/www/cache/TEST_MER_FRS.sqlite

# Upload test data
sudo cp /var/ngeob/autotest/data/reference_test_data/*.jpg /var/ngeob_data/storage/
sudo cp /var/ngeob/autotest/data/test_data/*.tif /var/ngeob_data/storage/
sudo cp /var/ngeob/autotest/data/feed_test_data/*.png /var/ngeob_data/storage/
sudo cp /var/ngeob/autotest/data/aiv_test_data/*.jpg /var/ngeob_data/storage/
sudo cp /var/ngeob/autotest/data/performance_test_data/*.jpg /var/ngeob_data/storage/

sudo service httpd start
