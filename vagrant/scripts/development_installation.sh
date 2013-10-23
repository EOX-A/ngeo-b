#!/bin/sh -e

# EOxServer
cd /var/eoxserver/
sudo python setup.py develop

# MapCache
cd /var/mapcache
mkdir -p build
cd build
cmake ..
make
sudo make install
if ! grep -Fxq "/usr/local/lib" /etc/ld.so.conf.d/mapcache.conf ; then
    echo "/usr/local/lib" >> /etc/ld.so.conf.d/mapcache.conf
fi
sudo ldconfig

# ngEO Browse Server
cd /var/ngeob/
sudo python setup.py develop

# Configure ngEO Browse Server autotest instance
cd /var/ngeob_autotest/

# Prepare DBs
python manage.py syncdb --noinput
python manage.py syncdb --database=mapcache --noinput
python manage.py loaddata initial_rangetypes.json

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

# Make the instance read- and editable by apache
chown -R apache:apache .


# TODO:
#chmod o+w /var/ngeob_autotest/logs/*.log
#loaddata
