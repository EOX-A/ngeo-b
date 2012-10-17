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

#INSTALL_DIR="/home/meissls/eox/projects/ESA_ngEO/Task4/git/deliverables/developments/ngeo_browse_server/" # TODO: Remove this line
INSTALL_DIR="/var/www/ngeo/"
APACHE_CONF="/etc/httpd/conf.d/010_ngeo_browse_server.conf"

# Check required tools are installed
if [ ! -x "`which sed`" ] ; then
    echo "ERROR: sed is required, please install it and try again" 
    exit 1
fi

# Install needed yum repositories
# EOX
if [ ! -f /etc/yum.repos.d/eox.repo ] ; then
    cd /etc/yum.repos.d/
    wget http://packages.eox.at/eox.repo
    rpm --import http://packages.eox.at/eox-package-maintainers.gpg
    cd -
fi
# EPEL
rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm
# ELGIS
rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

# Apply available upgrades
yum update -y

# Install packages
yum install -y gdal gdal-python mapserver mapserver-python pyspatialite \
    pysqlite Django mod_wsgi EOxServer ngEO_Browse_Server

if [ $? -ne 0 ] ; then
    echo "ERROR: Package installation failed! Aborting."
    exit 1
fi


[ -d "$INSTALL_DIR" ] || mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
chmod g+w .
chown apache:apache .


# Configure ngeo_browse_server_instance
if [ ! -d ngeo_browse_server_instance ] ; then

    django-admin.py startproject --extension=conf --template=/usr/lib/python2.6/site-packages/ngeo_browse_server/project_template/ ngeo_browse_server_instance # TODO: Adjust template path
    cd ngeo_browse_server_instance
    
#    spatialite ngeo_browse_server_instance/data/data.sqlite "SELECT InitSpatialMetaData();" # TODO

    # Configure logging
#    sed -e 's/#logging_level=/logging_level=INFO/' -i ngeo_browse_server_instance/conf/eoxserver.conf
#    sed -e 's/DEBUG = True/DEBUG = False/' -i ngeo_browse_server_instance/settings.py

    python manage.py syncdb --noinput

    python manage.py loaddata auth_data.json

#    sed -e 's,http_service_url=http://localhost:8000/ows,http_service_url=http://localhost/eoxserver/ows,' -i ngeo_browse_server_instance/conf/eoxserver.conf # TODO

    # Collect static files
    python manage.py collectstatic --noinput


    # Make the instance read- and editable by apache
    chown -R apache:apache .

    cd ..
fi


# Add Apache configuration
cat << EOF > "$APACHE_CONF"
<VirtualHost *:80>
    ServerName ngeo.eox.at
    ServerAdmin webmaster@eox.at

    DocumentRoot /var/www/html
    <Directory "/var/www/html/">
            Options Indexes FollowSymLinks
            AllowOverride None
            Order allow,deny
            Allow from all
    </Directory>

    Alias /static "$INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/static"
    Alias /b "$INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/wsgi.py"

    <Directory "$INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance">
        AllowOverride None
        Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
        AddHandler wsgi-script .py
        Order allow,deny
        allow from all
    </Directory>
</VirtualHost>
EOF

# Reload Apache
service httpd force-reload


echo "Finished ngEO Browse Server installation"
