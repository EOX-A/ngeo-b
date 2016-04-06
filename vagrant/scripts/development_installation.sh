#!/bin/sh -e
#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 European Space Agency
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

# EOxServer
cd /var/eoxserver/
python setup.py develop

# MapCache
cd /var/mapcache
mkdir -p build
cd build
cmake .. -DWITH_MEMCACHE=1
make
make install
if [ ! -f /etc/ld.so.conf.d/mapcache.conf ] || ! grep -Fxq "/usr/local/lib" /etc/ld.so.conf.d/mapcache.conf ; then
    echo "/usr/local/lib" >> /etc/ld.so.conf.d/mapcache.conf
fi
ldconfig

# ngEO Browse Server
cd /var/ngeob/
python setup.py develop

# Configure ngEO Browse Server autotest instance
cd /var/ngeob_autotest/

# Delete or reset old MapCache DB and configuration
rm -f /var/ngeob_autotest/data/mapcache.sqlite

python -c "
from lxml import etree
mapcache_xml_filename = '/var/www/cache/mapcache.xml'
root = etree.parse(mapcache_xml_filename).getroot()
for e in root.xpath('cache|source|tileset'):
    root.remove(e)
with open(mapcache_xml_filename, 'w') as f:
    f.write(etree.tostring(root, pretty_print=True))
"

# Prepare DBs
python manage.py syncdb --noinput
python manage.py syncdb --database=mapcache --noinput
python manage.py loaddata auth_data.json initial_rangetypes.json

# Reset ngEO Browse Server
rm -rf /var/ngeob_autotest/data/optimized/ /var/ngeob_autotest/data/success/ /var/ngeob_autotest/data/failure/ /var/www/store/
mkdir -p /var/ngeob_autotest/data/optimized/ /var/ngeob_autotest/data/success/ /var/ngeob_autotest/data/failure/ /var/www/store/
rm -f /var/ngeob_autotest/logs/eoxserver.log /var/ngeob_autotest/logs/ngeo.log /var/ngeob_autotest/logs/ingest.log /var/ngeob_autotest/logs/httpd_access.log /var/ngeob_autotest/logs/httpd_error.log
touch /var/ngeob_autotest/logs/eoxserver.log /var/ngeob_autotest/logs/ngeo.log /var/ngeob_autotest/logs/ingest.log /var/ngeob_autotest/logs/httpd_access.log /var/ngeob_autotest/logs/httpd_error.log

# Reset MapCache
rm -f /var/www/cache/SAR.sqlite /var/www/cache/OPTICAL.sqlite /var/www/cache/ASA_WSM.sqlite /var/www/cache/MER_FRS.sqlite /var/www/cache/MER_FRS_FULL.sqlite /var/www/cache/MER_FRS_FULL_NO_BANDS.sqlite /var/www/cache/GOOGLE_MERCATOR.sqlite

# Create admin user
TMPFILE=`mktemp`
cat << EOF > "$TMPFILE"
#!/usr/bin/env python
from os import environ
import sys

path = "/var/ngeob_autotest"
if path not in sys.path:
    sys.path.insert(0,path)
environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

user = authenticate(username='admin', password='admin')
if user is None:
    user = User.objects.create_user('admin', 'office@eox.at', 'admin')
EOF
if [ -f $TMPFILE ] ; then
    chmod +rx $TMPFILE
    "$TMPFILE"
    rm "$TMPFILE"
else
    echo "Script to add admin user not found."
fi

# Collect static files
python manage.py collectstatic --noinput

# Upload test data
cp /var/ngeob_autotest/data/reference_test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/test_data/*.tif /var/www/store/
cp /var/ngeob_autotest/data/test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/test_data/*.png /var/www/store/
cp /var/ngeob_autotest/data/feed_test_data/*.png /var/www/store/
cp /var/ngeob_autotest/data/aiv_test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/input_merge_test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/regular_grid_clipping/*.png /var/www/store/

# Make the instance read- and editable by apache
chmod -R a+w /var/ngeob_autotest/
chmod -R a+w /var/www/

# Add browse layers for testing
python manage.py ngeo_browse_layer data/layer_management/synchronizeConfiguration_defaultLayers.xml
#alternative method
#curl -d @data/layer_management/synchronizeConfiguration_defaultLayers.xml http://localhost/browse/config

# Make MapCache reread the configuration
service memcached restart
service httpd restart

NGEOB_LOG_DIR=/var/ngeob_autotest/logs
NGEO_REPORT_DIR=/var/www/store/reports
mkdir -p $NGEO_REPORT_DIR

cat << EOF > /etc/logrotate.d/ngeo
$NGEOB_LOG_DIR/httpd_access.log {
    daily
    rotate 14
    dateext
    missingok
    delaycompress
    compress
    postrotate
        /sbin/service httpd reload > /dev/null 2>/dev/null || true
        cd /var/ngeob_autotest/
        python manage.py ngeo_report --access-logfile=\$1-\`date +%Y%m%d\` --filename=$NGEO_REPORT_DIR/access_report_\`date --iso\`.xml
    endscript
}

$NGEOB_LOG_DIR/httpd_error.log {
    daily
    rotate 14
    dateext
    missingok
    notifempty
    delaycompress
    compress
    postrotate
        /sbin/service httpd reload > /dev/null 2>/dev/null || true
    endscript
}

$NGEOB_LOG_DIR/ingest.log {
    daily
    rotate 14
    dateext
    missingok
    delaycompress
    compress
    postrotate
    	cd /var/ngeob_autotest/
        python manage.py ngeo_report --report-logfile=\$1-\`date +%Y%m%d\` --filename=$NGEO_REPORT_DIR/ingest_report_\`date --iso\`.xml
    endscript
}

$NGEOB_LOG_DIR/eoxserver.log $NGEOB_LOG_DIR/ngeo.log {
    daily
    rotate 14
    dateext
    missingok
    notifempty
    delaycompress
    compress
}
EOF
