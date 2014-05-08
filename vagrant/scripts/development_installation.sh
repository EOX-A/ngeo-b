#!/bin/sh -e

# EOxServer
cd /var/eoxserver/
python setup.py develop --disable-extended-reftools

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

# Prepare DBs
python manage.py syncdb --noinput
python manage.py syncdb --database=mapcache --noinput
python manage.py loaddata auth_data.json initial_rangetypes.json


python manage.py ngeo_browse_layer --add /var/ngeob_autotest/data/layer_management/defaultLayers.xml

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

# Create runtime files
mkdir -p /var/ngeob_autotest/data/optimized/ /var/ngeob_autotest/data/success/ /var/ngeob_autotest/data/failure/ /var/www/store/
touch /var/ngeob_autotest/logs/eoxserver.log /var/ngeob_autotest/logs/ngeo.log


# Upload test data
cp /var/ngeob_autotest/data/reference_test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/test_data/*.tif /var/www/store/
cp /var/ngeob_autotest/data/test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/feed_test_data/*.png /var/www/store/
cp /var/ngeob_autotest/data/aiv_test_data/*.jpg /var/www/store/

# Make the instance read- and editable by everybody
chmod -R a+w /var/ngeob_autotest/
chmod -R a+w /var/www/

NGEOB_LOG_DIR=/var/ngeob_autotest/logs
NGEO_REPORT_DIR=/var/www/store/reports
mkdir -p $NGEO_REPORT_DIR

cat << EOF > /etc/logrotate.d/ngeo
$NGEOB_LOG_DIR/httpd_access.log {
    missingok
    notifempty
    delaycompress
    postrotate
        /sbin/service httpd reload > /dev/null 2>/dev/null || true
        cd /var/ngeob_autotest/
        python manage.py ngeo_report --access-logfile=\$1.1 --filename=$NGEO_REPORT_DIR/access_report_\`date --iso\`.xml
    endscript
}

$NGEOB_LOG_DIR/httpd_error.log {
    missingok
    notifempty
    delaycompress
    postrotate
        /sbin/service httpd reload > /dev/null 2>/dev/null || true
    endscript
}

$NGEOB_LOG_DIR/ingest.log {
    missingok
    notifempty
    delaycompress
    postrotate
    	cd /var/ngeob_autotest/
        python manage.py ngeo_report --report-logfile=\$1.1 --filename=$NGEO_REPORT_DIR/ingest_report_\`date --iso\`.xml
    endscript
}

$NGEOB_LOG_DIR/eoxserver.log $NGEOB_LOG_DIR/ngeo.log {
    missingok
    notifempty
    delaycompress
}
EOF