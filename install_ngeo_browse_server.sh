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

# Running:
# =======
# sudo ./install_ngeo_browse_server.sh

################################################################################
# Adjust the variables to your liking.                                         #
################################################################################

# ngEO Browse Server
NGEOB_INSTALL_DIR="/var/www/ngeo"
NGEOB_URL="http://ngeo.eox.at"

# PostgreSQL/PostGIS database
DB_NAME="ngeo_browse_server_db"
DB_USER="ngeo_user"
DB_PASSWORD="oi4Zuush"

# MapCache
MAPCACHE_DIR="/var/www/cache"

# Apache HTTPD
APACHE_CONF="/etc/httpd/conf.d/010_ngeo_browse_server.conf"
APACHE_ServerName="ngeo.eox.at"
APACHE_ServerAdmin="webmaster@eox.at"
APACHE_NGEO_BROWSE_ALIAS="/browse"

################################################################################
# Usually there should be no need to change anything below.                    #
################################################################################

echo "==============================================================="
echo "install_ngeo_browse_server.sh"
echo "==============================================================="

echo "Starting ngEO Browse Server installation"

# Check architecture
if [ "`uname -m`" != "x86_64" ] ; then
   echo "ERROR: Current system is not x86_64 but `uname -m`. Script was 
         implemented for x86_64 only."
   exit 1
fi

# Check required tools are installed
if [ ! -x "`which sed`" ] ; then
    echo "ERROR: sed is required, please install it and try again" 
    exit 1
fi


# Disable SELinux
setenforce 0
if ! grep -Fxq "^SELINUX=enforcing$" /etc/selinux/config ; then
    sed -e 's/^SELINUX=enforcing$/SELINUX=disabled/' -i /etc/selinux/config
fi


# Install needed yum repositories
# EOX
if [ ! -f /etc/yum.repos.d/eox.repo ] ; then
    cd /etc/yum.repos.d/
    wget -c --progress=dot:mega \
        "http://packages.eox.at/eox.repo"
    rpm --import http://packages.eox.at/eox-package-maintainers.gpg
    cd -
fi
# Set includepkgs
if ! grep -Fxq "includepkgs=EOxServer pyspatialite pysqlite libxml2 libxml2-python" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox\]$/&\nincludepkgs=EOxServer pyspatialite pysqlite libxml2 libxml2-python/' -i /etc/yum.repos.d/eox.repo
fi
if ! grep -Fxq "includepkgs=ngEO_Browse_Server" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox-noarch\]$/&\nincludepkgs=ngEO_Browse_Server/' -i /etc/yum.repos.d/eox.repo
fi
# Set exclude
if ! grep -Fxq "exclude=libxml2 libxml2-python" /etc/yum.repos.d/CentOS-Base.repo ; then
    sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python/' -i /etc/yum.repos.d/CentOS-Base.repo
    sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python/' -i /etc/yum.repos.d/CentOS-Base.repo
fi
# EPEL
rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm
# ELGIS
rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

# TODO MapServer 6.0.3 dependencies
wget -c --progress=dot:mega \
    "http://dl.atrpms.net/all/bitstream-vera-fonts-common-1.10-18.el6.noarch.rpm"
wget -c --progress=dot:mega \
    "http://dl.atrpms.net/all/bitstream-vera-sans-fonts-1.10-18.el6.noarch.rpm"
yum install fontpackages-filesystem
rpm -Uhv bitstream-vera-fonts-common-1.10-18.el6.noarch.rpm \
    bitstream-vera-sans-fonts-1.10-18.el6.noarch.rpm

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


# Permanently start PostgreSQL
chkconfig postgresql on

# Init PostgreSQL
if [ ! -f "/var/lib/pgsql/data/PG_VERSION" ] ; then
    service postgresql initdb
fi

# Allow DB_USER to access DB_NAME with password
if ! grep -Fxq "local   $DB_NAME $DB_USER               md5" /var/lib/pgsql/data/pg_hba.conf ; then
    sed -e "s/^# \"local\" is for Unix domain socket connections only$/&\nlocal   $DB_NAME $DB_USER               md5/" -i /var/lib/pgsql/data/pg_hba.conf
fi

# Reload PostgreSQL
service postgresql force-reload

# Configure PostgreSQL/PostGIS database
if [ -f db_config_ngeo_browse_server.sh ] ; then
    chgrp postgres db_config_ngeo_browse_server.sh
    chmod g+x db_config_ngeo_browse_server.sh
    su postgres -c "./db_config_ngeo_browse_server.sh $DB_NAME $DB_USER  $DB_PASSWORD"
else
    echo "Script db_config_ngeo_browse_server.sh to configure DB not found."
fi


[ -d "$NGEOB_INSTALL_DIR" ] || mkdir -p "$NGEOB_INSTALL_DIR"
cd "$NGEOB_INSTALL_DIR"


# Configure ngeo_browse_server_instance
if [ ! -d ngeo_browse_server_instance ] ; then

    django-admin startproject --extension=conf --template=`python -c "import ngeo_browse_server, os; from os.path import dirname, abspath, join; print(join(dirname(abspath(ngeo_browse_server.__file__)), 'project_template'))"` ngeo_browse_server_instance
    cd ngeo_browse_server_instance
    
    # Configure logging
#    sed -e 's/#logging_level=/logging_level=INFO/' -i ngeo_browse_server_instance/conf/eoxserver.conf # TODO enable in production
#    sed -e 's/DEBUG = True/DEBUG = False/' -i ngeo_browse_server_instance/settings.py # TODO enable in production

    # Configure DBs
    NGEOB_INSTALL_DIR_ESCAPED=`echo $NGEOB_INSTALL_DIR | sed -e 's/\//\\\&/g'`
    sed -e "s/'ENGINE': 'django.contrib.gis.db.backends.spatialite',                  # Use 'spatialite' or change to 'postgis'./'ENGINE': 'django.contrib.gis.db.backends.postgis',/" -i ngeo_browse_server_instance/settings.py
    sed -e "s/'NAME': '$NGEOB_INSTALL_DIR_ESCAPED\/ngeo_browse_server_instance\/ngeo_browse_server_instance\/data\/data.sqlite',  # Or path to database file if using spatialite./'NAME': '$DB_NAME',/" -i ngeo_browse_server_instance/settings.py
    sed -e "s/'USER': '',                                                             # Not used with spatialite./'USER': '$DB_USER',/" -i ngeo_browse_server_instance/settings.py
    sed -e "s/'PASSWORD': '',                                                         # Not used with spatialite./'PASSWORD': '$DB_PASSWORD',/" -i ngeo_browse_server_instance/settings.py
    sed -e "/#'TEST_NAME': '$NGEOB_INSTALL_DIR_ESCAPED\/ngeo_browse_server_instance\/ngeo_browse_server_instance\/data\/test-config.sqlite', # Required for certain test cases, but slower!/d" -i ngeo_browse_server_instance/settings.py
    sed -e "/'HOST': '',                                                             # Set to empty string for localhost. Not used with spatialite./d" -i ngeo_browse_server_instance/settings.py
    sed -e "/'PORT': '',                                                             # Set to empty string for default. Not used with spatialite./d" -i ngeo_browse_server_instance/settings.py

    python manage.py syncdb --noinput
    python manage.py syncdb --database=mapcache --noinput
    python manage.py loaddata initial_rangetypes.json
    
    python manage.py loaddata auth_data.json ngeo_browse_layer.json eoxs_dataset_series.json # TODO remove in production
    python manage.py loaddata --database=mapcache ngeo_mapcache.json # TODO remove in production

    sed -e "s,http_service_url=http://localhost:8000/ows,http_service_url=$NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/ows," -i ngeo_browse_server_instance/conf/eoxserver.conf

    # Collect static files
    python manage.py collectstatic --noinput

    # Make the instance read- and editable by apache
    chown -R apache:apache .

    cd ..
fi


# Configure MapCache
[ -d "$MAPCACHE_DIR" ] || mkdir -p "$MAPCACHE_DIR"
cd "$MAPCACHE_DIR"

#TODO

# Make the cache read- and editable by apache
chown -R apache:apache .


# Configure WebDAV
[ -d "$NGEOB_INSTALL_DIR/store" ] || mkdir -p "$NGEOB_INSTALL_DIR/store"


# Add Apache configuration
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

    <Directory "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance">
        AllowOverride None
        Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
        AddHandler wsgi-script .py
        Order allow,deny
        allow from all
    </Directory>

    # TODO finish
    # Alias /c "$MAPCACHE_DIR"

    # TODO use vars in beginning of script
    DavLockDB /var/www/dav/DavLock
    Alias /store "$NGEOB_INSTALL_DIR/store"
    <Directory $NGEOB_INSTALL_DIR/store>
        Order Allow,Deny
        Allow from all
        Dav On
        Options +Indexes

        AuthType Digest
        AuthName "dav@ngeo.eox.at"
        AuthDigestDomain /store/ http://ngeo.eox.at/store/

        AuthDigestProvider file
        AuthUserFile /var/www/dav/DavUsers
        Require valid-user
    </Directory>
</VirtualHost>
EOF

# Permanently start Apache
chkconfig httpd on

# Reload Apache
service httpd graceful


echo "Finished ngEO Browse Server installation"
