#!/bin/sh -e

# Update all the installed packages
yum update -y

# Install packages
cd "/var/ngeob/install/local_packages"
yum install -y Django14-1.4.21-1.el6.noarch.rpm \
               geos-3.3.8-2.el6.x86_64.rpm \
               libspatialite-2.4.0-0.6_0.RC4.el6.x86_64.rpm \
               libtiff4-4.0.3-1.el6.x86_64.rpm \
               postgis-1.5.8-1.el6.x86_64.rpm \
               proj-4.8.0-3.el6.x86_64.rpm \
               proj-epsg-4.8.0-3.el6.x86_64.rpm
cd -
yum install -y gdal-eox-libtiff4 gdal-eox-libtiff4-python \
               gdal-eox-libtiff4-java gdal-eox-driver-openjpeg2 \
               libgeotiff-libtiff4
yum install -y python-lxml mod_wsgi httpd postgresql-server python-psycopg2 pytz
yum install -y libxml2 libxml2-python mapserver mapserver-python

# Install some build dependencies
yum install -y gcc make gcc-c++ kernel-devel-`uname -r` zlib-devel \
               openssl-devel readline-devel perl wget httpd-devel pixman-devel \
               sqlite-devel libpng-devel libjpeg-devel libcurl-devel cmake \
               fcgi-devel gdal-eox-libtiff4-devel python-devel \
               memcached

# Attention: Make sure to not install mapcache, ngEO_Browse_Server, and
# EOxServer from rpm packages!
# See development_installation.sh for installation.
