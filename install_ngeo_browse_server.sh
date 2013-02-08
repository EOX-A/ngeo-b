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
# This script installs the ngEO Browse Server.
#
# Use with caution as passwords are sent on the command line and thus can be 
# seen by other users.

# Running:
# =======
# sudo ./install_ngeo_browse_server.sh

################################################################################
# Adjust the variables to your liking.                                         #
################################################################################

# Enable/disable testing repositories (false..disable; true..enable)
TESTING=true

# ngEO Browse Server
NGEOB_INSTALL_DIR="/var/www/ngeo"
NGEOB_URL="http://ngeo.eox.at"

# PostgreSQL/PostGIS database
DB_NAME="ngeo_browse_server_db"
DB_USER="ngeo_user"
DB_PASSWORD="oi4Zuush"

# MapCache
MAPCACHE_DIR="/var/www/cache"
MAPCACHE_CONF="mapcache.xml"

# Apache HTTPD
APACHE_CONF="/etc/httpd/conf.d/010_ngeo_browse_server.conf"
APACHE_ServerName="ngeo.eox.at"
APACHE_ServerAdmin="webmaster@eox.at"
APACHE_NGEO_BROWSE_ALIAS="/browse"
APACHE_NGEO_CACHE_ALIAS="/c"
APACHE_NGEO_STORE_ALIAS="/store"

# WebDAV
WEBDAV_USER="test"
WEBDAV_PASSWORD="eiNoo7ae"

# Django
DJANGO_USER="admin"
DJANGO_MAIL="ngeo@eox.at"
DJANGO_PASSWORD="Aa2phu0s"

################################################################################
# Usually there should be no need to change anything below.                    #
################################################################################

echo "==============================================================="
echo "install_ngeo_browse_server.sh"
echo "==============================================================="

echo "Started ngEO Browse Server installation"

# Check architecture
if [ "`uname -m`" != "x86_64" ] ; then
   echo "ERROR: Current system is not x86_64 but `uname -m`. Script was 
         implemented for x86_64 only."
   exit 1
fi

# Check required tools are installed
if [ ! -x "`which sed`" ] ; then
    yum install -y sed
fi


# Disable SELinux
setenforce 0
if ! grep -Fxq "^SELINUX=enforcing$" /etc/selinux/config ; then
    sed -e 's/^SELINUX=enforcing$/SELINUX=disabled/' -i /etc/selinux/config
fi


# Install needed yum repositories
# EOX
rpm -Uvh http://yum.packages.eox.at/el/eox-release-6-1.noarch.rpm
if "$TESTING" ; then
    sed -e 's/^enabled=0/enabled=1/' -i /etc/yum.repos.d/eox-testing.repo
fi
# Set includepkgs in EOX Stable
if ! grep -Fxq "includepkgs=EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox\]$/&\nincludepkgs=EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python/' -i /etc/yum.repos.d/eox.repo
fi
if ! grep -Fxq "includepkgs=ngEO_Browse_Server" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox-noarch\]$/&\nincludepkgs=ngEO_Browse_Server/' -i /etc/yum.repos.d/eox.repo
fi
# Set includepkgs in EOX Testing
if ! grep -Fxq "includepkgs=EOxServer mapcache" /etc/yum.repos.d/eox-testing.repo ; then
    sed -e 's/^\[eox-testing\]$/&\nincludepkgs=EOxServer mapcache/' -i /etc/yum.repos.d/eox-testing.repo
fi
if ! grep -Fxq "includepkgs=ngEO_Browse_Server" /etc/yum.repos.d/eox-testing.repo ; then
    sed -e 's/^\[eox-testing-noarch\]$/&\nincludepkgs=ngEO_Browse_Server/' -i /etc/yum.repos.d/eox-testing.repo
fi
# Set exclude in CentOS-Base
if ! grep -Fxq "exclude=libxml2 libxml2-python" /etc/yum.repos.d/CentOS-Base.repo ; then
    sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python/' -i /etc/yum.repos.d/CentOS-Base.repo
    sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python/' -i /etc/yum.repos.d/CentOS-Base.repo
fi
# EPEL
rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
# ELGIS
rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

# Apply available upgrades
yum update -y

# Install packages
yum install -y gdal gdal-python mapserver mapserver-python postgis \
    postgresql-server python-psycopg2 Django14 httpd mod_wsgi libxml2 \
    libxml2-python python-lxml pytz mapcache \
    EOxServer ngEO_Browse_Server

if [ $? -ne 0 ] ; then
    echo "ERROR: Package installation failed! Aborting."
    exit 1
fi


# Permanently start Apache
chkconfig httpd on

# Permanently start PostgreSQL
chkconfig postgresql on


# Init PostgreSQL
if [ ! -f "/var/lib/pgsql/data/PG_VERSION" ] ; then
    service postgresql initdb
fi

# Allow DB_USER to access DB_NAME and test_DB_NAME with password
if ! grep -Fxq "local   $DB_NAME $DB_USER               md5" /var/lib/pgsql/data/pg_hba.conf ; then
    sed -e "s/^# \"local\" is for Unix domain socket connections only$/&\nlocal   $DB_NAME $DB_USER               md5\nlocal   test_$DB_NAME $DB_USER          md5/" \
		-i /var/lib/pgsql/data/pg_hba.conf
fi

# Reload PostgreSQL
service postgresql force-reload

# Configure PostgreSQL/PostGIS database

## Write database configuration script
TMPFILE=`mktemp`
cat << EOF > "$TMPFILE"
#!/bin/sh
# cd to a "safe" location
cd /tmp
if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='template_postgis'")" != 1 ] ; then
    echo "Creating template database."
    createdb -E UTF8 template_postgis
    createlang plpgsql -d template_postgis
    psql postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
    psql -d template_postgis -f /usr/share/pgsql/contrib/postgis.sql
    psql -d template_postgis -f /usr/share/pgsql/contrib/spatial_ref_sys.sql
    psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
    psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
fi
if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")" != 1 ] ; then
    echo "Creating ngEO database user."
    psql postgres -tAc "CREATE USER $DB_USER NOSUPERUSER CREATEDB NOCREATEROLE ENCRYPTED PASSWORD '$DB_PASSWORD'"
fi
if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")" != 1 ] ; then
    echo "Creating ngEO Browse Server database."
    createdb -O $DB_USER -T template_postgis $DB_NAME
fi
EOF
## End of database configuration script

if [ -f $TMPFILE ] ; then
    chgrp postgres $TMPFILE
    chmod g+rx $TMPFILE
    su postgres -c "$TMPFILE"
    rm "$TMPFILE"
else
    echo "Script to configure DB not found."
fi


# ngEO Browse Server
[ -d "$NGEOB_INSTALL_DIR" ] || mkdir -p "$NGEOB_INSTALL_DIR"
cd "$NGEOB_INSTALL_DIR"

# Configure ngeo_browse_server_instance
if [ ! -d ngeo_browse_server_instance ] ; then
    echo "Creating and configuring ngEO Browse Server instance."

    django-admin startproject --extension=conf --template=`python -c "import ngeo_browse_server, os; from os.path import dirname, abspath, join; print(join(dirname(abspath(ngeo_browse_server.__file__)), 'project_template'))"` ngeo_browse_server_instance
    cd ngeo_browse_server_instance
    
    # Configure DBs
    NGEOB_INSTALL_DIR_ESCAPED=`echo $NGEOB_INSTALL_DIR | sed -e 's/\//\\\&/g'`
    sed -e "s/'ENGINE': 'django.contrib.gis.db.backends.spatialite',                  # Use 'spatialite' or change to 'postgis'./'ENGINE': 'django.contrib.gis.db.backends.postgis',/" -i ngeo_browse_server_instance/settings.py
    sed -e "s/'NAME': '$NGEOB_INSTALL_DIR_ESCAPED\/ngeo_browse_server_instance\/ngeo_browse_server_instance\/data\/data.sqlite',  # Or path to database file if using spatialite./'NAME': '$DB_NAME',/" -i ngeo_browse_server_instance/settings.py
    sed -e "s/'USER': '',                                                             # Not used with spatialite./'USER': '$DB_USER',/" -i ngeo_browse_server_instance/settings.py
    sed -e "s/'PASSWORD': '',                                                         # Not used with spatialite./'PASSWORD': '$DB_PASSWORD',/" -i ngeo_browse_server_instance/settings.py
    sed -e "/#'TEST_NAME': '$NGEOB_INSTALL_DIR_ESCAPED\/ngeo_browse_server_instance\/ngeo_browse_server_instance\/data\/test-data.sqlite', # Required for certain test cases, but slower!/d" -i ngeo_browse_server_instance/settings.py
    sed -e "/'HOST': '',                                                             # Set to empty string for localhost. Not used with spatialite./d" -i ngeo_browse_server_instance/settings.py
    sed -e "/'PORT': '',                                                             # Set to empty string for default. Not used with spatialite./d" -i ngeo_browse_server_instance/settings.py
    sed -e "s/#'TEST_NAME': '$NGEOB_INSTALL_DIR_ESCAPED\/ngeo_browse_server_instance\/ngeo_browse_server_instance\/data\/test-mapcache.sqlite',/'TEST_NAME': '$NGEOB_INSTALL_DIR_ESCAPED\/ngeo_browse_server_instance\/ngeo_browse_server_instance\/data\/test-mapcache.sqlite',/" -i ngeo_browse_server_instance/settings.py

    # Configure instance
    sed -e "s,http_service_url=http://localhost:8000/ows,http_service_url=$NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/ows," -i ngeo_browse_server_instance/conf/eoxserver.conf
    MAPCACHE_DIR_ESCAPED=`echo $MAPCACHE_DIR | sed -e 's/\//\\\&/g'`
    sed -e "s/^tileset_root=$/tileset_root=$MAPCACHE_DIR_ESCAPED\//" -i ngeo_browse_server_instance/conf/ngeo.conf
    sed -e "s/^config_file=$/config_file=$MAPCACHE_DIR_ESCAPED\/seed_$MAPCACHE_CONF/" -i ngeo_browse_server_instance/conf/ngeo.conf
    sed -e "s/^storage_dir=data\/storage$/storage_dir=$NGEOB_INSTALL_DIR_ESCAPED\/store/" -i ngeo_browse_server_instance/conf/ngeo.conf
    
    if ! "$TESTING" ; then
        # Configure logging
        sed -e 's/#logging_level=/logging_level=INFO/' -i ngeo_browse_server_instance/conf/eoxserver.conf
        sed -e 's/DEBUG = True/DEBUG = False/' -i ngeo_browse_server_instance/settings.py
    fi

    # Prepare DBs
    python manage.py syncdb --noinput
    python manage.py syncdb --database=mapcache --noinput
    python manage.py loaddata initial_rangetypes.json

    # Create admin user
    python manage.py createsuperuser --username=$DJANGO_USER --email=$DJANGO_MAIL --noinput
    python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ngeo_browse_server_instance.settings'); \
               from django.contrib.auth.models import User;  admin = User.objects.get(username='$DJANGO_USER'); \
               admin.set_password('$DJANGO_PASSWORD'); admin.save();"

    # Collect static files
    python manage.py collectstatic --noinput

    # Make the instance read- and editable by apache
    chown -R apache:apache .

    cd ..
fi


# MapCache
if [ ! -d "$MAPCACHE_DIR" ] ; then
    echo "Configuring MapCache."

    mkdir -p "$MAPCACHE_DIR"
    cd "$MAPCACHE_DIR"

    # Configure read-only MapCache
    cat << EOF > "$MAPCACHE_DIR/$MAPCACHE_CONF"
<?xml version="1.0" encoding="UTF-8"?>
<mapcache>
    <default_format>mixed</default_format>
    <format name="mypng" type ="PNG">
        <compression>fast</compression>
    </format>
    <format name="myjpeg" type ="JPEG">
        <quality>85</quality>
        <photometric>ycbcr</photometric>
    </format>
    <format name="mixed" type="MIXED">
        <transparent>mypng</transparent>
        <opaque>myjpeg</opaque>
    </format>

    <service type="wms" enabled="true">
        <full_wms>assemble</full_wms>
        <resample_mode>bilinear</resample_mode>
        <format>JPEG</format>
        <maxsize>4096</maxsize>
    </service>
    <service type="wmts" enabled="true"/>

    <errors>empty_img</errors>
    <lock_dir>/tmp</lock_dir>
</mapcache>
EOF
    # Configure second MapCache instance for seeding
    cat << EOF > "$MAPCACHE_DIR/seed_$MAPCACHE_CONF"
<?xml version="1.0" encoding="UTF-8"?>
<mapcache>
    <default_format>mixed</default_format>
    <format name="mypng" type ="PNG">
        <compression>fast</compression>
    </format>
    <format name="myjpeg" type ="JPEG">
        <quality>85</quality>
        <photometric>ycbcr</photometric>
    </format>
    <format name="mixed" type="MIXED">
        <transparent>mypng</transparent>
        <opaque>myjpeg</opaque>
    </format>

    <service type="wms" enabled="true">
        <full_wms>assemble</full_wms>
        <resample_mode>bilinear</resample_mode>
        <format>JPEG</format>
        <maxsize>4096</maxsize>
    </service>
    <service type="wmts" enabled="true"/>

    <errors>empty_img</errors>
    <lock_dir>/tmp</lock_dir>
</mapcache>
EOF

    # Make the cache read- and editable by apache
    chown -R apache:apache .

    cd -
fi


# Configure WebDAV
if [ ! -d "$NGEOB_INSTALL_DIR/dav" ] ; then
    echo "Configuring WebDAV."
    mkdir -p "$NGEOB_INSTALL_DIR/dav"
    printf "$WEBDAV_USER:ngEO Browse Server:$WEBDAV_PASSWORD" | md5sum - > $NGEOB_INSTALL_DIR/dav/DavUsers
    sed -e "s/^\(.*\)  -$/test:ngEO Browse Server:\1/" -i $NGEOB_INSTALL_DIR/dav/DavUsers
    chown -R apache:apache "$NGEOB_INSTALL_DIR/dav"
    chmod 0640 "$NGEOB_INSTALL_DIR/dav/DavUsers"
fi
if [ ! -d "$NGEOB_INSTALL_DIR/store" ] ; then
    mkdir -p "$NGEOB_INSTALL_DIR/store"
    chown -R apache:apache "$NGEOB_INSTALL_DIR/store"
fi

# Enable MapCache module in Apache
if ! grep -Fxq "LoadModule mapcache_module modules/mod_mapcache.so" /etc/httpd/conf/httpd.conf ; then
    sed -e 's/^LoadModule version_module modules\/mod_version.so$/&\nLoadModule mapcache_module modules\/mod_mapcache.so/' -i /etc/httpd/conf/httpd.conf
fi


# Add Apache configuration
if [ ! -f "$APACHE_CONF" ] ; then
    echo "Configuring Apache."

    # Configure WSGI module
    if ! grep -Fxq "WSGISocketPrefix run/wsgi" /etc/httpd/conf.d/wsgi.conf ; then
        echo "WSGISocketPrefix run/wsgi" >> /etc/httpd/conf.d/wsgi.conf
    fi

    # Add hostname
    HOSTNAME=`hostname`
    if ! grep -Gxq "127\.0\.0\.1.* $HOSTNAME" /etc/hosts ; then
        sed -e "s/^127\.0\.0\.1.*$/& $HOSTNAME/" -i /etc/hosts
    fi

    cat << EOF > "$APACHE_CONF"
<VirtualHost *:80>
    ServerName $APACHE_ServerName
    ServerAdmin $APACHE_ServerAdmin

    DocumentRoot $NGEOB_INSTALL_DIR
    <Directory "$NGEOB_INSTALL_DIR">
            Options Indexes FollowSymLinks
            AllowOverride None
            Order deny,allow
            Deny from all
    </Directory>

    Alias /static "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/static"
    Alias $APACHE_NGEO_BROWSE_ALIAS "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/wsgi.py"

    WSGIDaemonProcess ngeob processes=10 threads=1
    <Directory "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance">
        AllowOverride None
        Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
        AddHandler wsgi-script .py
        WSGIProcessGroup ngeob
        Order allow,deny
        allow from all
    </Directory>

    MapCacheAlias $APACHE_NGEO_CACHE_ALIAS "$MAPCACHE_DIR/mapcache.xml"
    <Directory $MAPCACHE_DIR>
        Order Allow,Deny
        Allow from all
        Header set Access-Control-Allow-Origin *
    </Directory>

    DavLockDB "$NGEOB_INSTALL_DIR/dav/DavLock"
    Alias $APACHE_NGEO_STORE_ALIAS "$NGEOB_INSTALL_DIR/store"
    <Directory $NGEOB_INSTALL_DIR/store>
        Order Allow,Deny
        Allow from all
        Dav On
        Options +Indexes

        AuthType Digest
        AuthName "ngEO Browse Server"
        AuthDigestDomain $APACHE_NGEO_STORE_ALIAS $NGEOB_URL$APACHE_NGEO_STORE_ALIAS
        AuthDigestProvider file
        AuthUserFile "$NGEOB_INSTALL_DIR/dav/DavUsers"
        Require valid-user
    </Directory>
    <Directory $NGEOB_INSTALL_DIR/dav>
        Order Allow,Deny
        Deny from all
    </Directory>
</VirtualHost>
EOF
fi

# Reload Apache
service httpd graceful

echo "Finished ngEO Browse Server installation"
