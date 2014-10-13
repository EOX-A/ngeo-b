#!/bin/sh

# Install the EPEL repository
yum install epel-release

# Install the ELGIS repository
rpm -Uvh --replacepkgs http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

# Install and enable the EOX repository
rpm -Uvh --replacepkgs http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
sed -e 's/^enabled=0/enabled=1/' -i /etc/yum.repos.d/eox-testing.repo

# Ignore TU Vienna CentOS mirror
sed -e 's/^#exclude=.*/exclude=gd.tuwien.ac.at/' /etc/yum/pluginconf.d/fastestmirror.conf > /etc/yum/pluginconf.d/fastestmirror.conf

# Set includepkgs in EOX Stable
if ! grep -Fxq "includepkgs=gdal gdal-python gdal-libs gdal-devel gdal-java EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox\]$/&\nincludepkgs=gdal gdal-python gdal-libs gdal-devel gdal-java EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/eox.repo
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
    sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
    sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
fi

# Install Continuous Release (CR) repository
yum install -y centos-release-cr
