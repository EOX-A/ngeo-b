#!/bin/sh -e

# EOxServer
cd /var/eoxserver/
python setup.py develop

# MapCache
cd /var/mapcache
mkdir -p build
cd build
cmake ..
make
make install
if ! grep -Fxq "/usr/local/lib" /etc/ld.so.conf.d/mapcache.conf ; then
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
python manage.py loaddata auth_data.json ngeo_browse_layer.json eoxs_dataset_series.json initial_rangetypes.json
python manage.py loaddata --database=mapcache ngeo_mapcache.json

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
touch /var/www/cache/TEST_SAR.sqlite /var/www/cache/TEST_OPTICAL.sqlite /var/www/cache/TEST_ASA_WSM.sqlite /var/www/cache/TEST_MER_FRS.sqlite /var/www/cache/TEST_MER_FRS_FULL.sqlite /var/www/cache/TEST_MER_FRS_FULL_NO_BANDS.sqlite /var/www/cache/TEST_GOOGLE_MERCATOR.sqlite

# Upload test data
cp /var/ngeob_autotest/data/reference_test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/test_data/*.tif /var/www/store/
cp /var/ngeob_autotest/data/test_data/*.jpg /var/www/store/
cp /var/ngeob_autotest/data/feed_test_data/*.png /var/www/store/
cp /var/ngeob_autotest/data/aiv_test_data/*.jpg /var/www/store/

# Make the instance read- and editable by everybody
chmod -R a+w /var/ngeob_autotest/
chmod -R a+w /var/www/

service httpd restart
