#!/bin/sh -e
#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012, 2013 EOX IT Services GmbH
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

################################################################################
# @maintained by: EOX IT Services GmbH
# @project NGEO T4
# @version 1.0
# @date 2013-07-09
# @purpose This script installs/uninstalls the ngEO Browse Server
#
#          Use with caution as passwords are sent on the command line and thus
#          can be seen by other users.
#
#          References are given to the steps defined in the Installation,
#          Operation, and Maintenance Manual (IOM) [ngEO-BROW-IOM] section 4.3.
#
# Usage:
# - Installation: sudo ./ngeo-install.sh install
# - Un-installation: sudo ./ngeo-install.sh uninstall
# - Full un-installation including data: sudo ./ngeo-install.sh  full_uninstall
# - Installation status: sudo ./ngeo-install.sh status
################################################################################

# ------------------------------------------------------------------------------
# Configuration section
# ------------------------------------------------------------------------------

# Subsystem name
SUBSYSTEM="ngEO Browse Server"

# Enable/disable testing repositories, debug logging, etc.
# (false..disable; true..enable)
TESTING=false

# ngEO Browse Server
NGEOB_INSTANCE_ID="autotest"
NGEOB_INSTALL_DIR="/var/www/ngeo"
NGEOB_URL="http://ngeo.eox.at"
NGEOB_LOG_DIR="$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/logs"
NGEO_REPORT_DIR="$NGEOB_INSTALL_DIR/store/reports"

# PostgreSQL/PostGIS database
DB_NAME="ngeo_browse_server_db"
DB_USER="ngeo_user"
DB_PASSWORD="oi4Zuush"

# MapCache
MAPCACHE_DIR="/var/www/cache"
MAPCACHE_CONF="mapcache.xml"
MAPCACHE_USER_HEADER="SP-Person-Identifier"

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

# ------------------------------------------------------------------------------
# End of configuration section
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Install
# ------------------------------------------------------------------------------
ngeo_install() {

    echo "------------------------------------------------------------------------------"
    echo " $SUBSYSTEM Install"
    echo "------------------------------------------------------------------------------"

    echo "Performing installation step 0"
    echo "Uninstalling any previous version"
    ngeo_uninstall

    echo "Starting ngEO Browse Server installation"
    echo "Assuming successful execution of installation steps 10, 20, and 30"

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


    #-----------------
    # OS installation
    #-----------------

    echo "Setting timezone to UTC"
    rm -f /etc/localtime
    cp /usr/share/zoneinfo/UTC /etc/localtime
    cat << EOF > /etc/sysconfig/clock
ZONE="UTC"
EOF

    echo "Performing installation step 40"
    # Disable SELinux
    if ! [ `getenforce` == "Disabled" ] ; then
        setenforce 0
    fi
    if ! grep -Fxq "SELINUX=disabled" /etc/selinux/config ; then
        sed -e 's/^SELINUX=.*$/SELINUX=disabled/' -i /etc/selinux/config
    fi

    echo "Performing installation step 50"
    # Install packages
    yum install -y python-lxml mod_wsgi httpd memcached postgresql-server python-psycopg2 pytz lftp unzip

    echo "Performing installation step 60"
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

    echo "Performing installation step 70"
    # Permanently start memcached, prior to apache
    chkconfig memcached on --levels 12345

    # Permanently start Apache
    chkconfig httpd on
    # Reload Apache
    service httpd graceful


    #-----------------------
    # OSS/COTS installation
    #-----------------------

    echo "Assuming successful execution of installation step 80"

    # Install needed yum repositories
    echo "Performing installation step 90"
    # EPEL
    yum install -y epel-release
    rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

    echo "Performing installation step 100"
    # ELGIS
    rpm -Uvh --replacepkgs http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
    rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-ELGIS

    echo "Performing installation step 110"
    # Apply available upgrades
    yum update -y

    echo "Performing installation step 120"
    # Install packages
    yum install -y postgis Django14 proj-epsg


    #------------------------
    # Component installation
    #------------------------

    echo "Assuming successful execution of installation step 130"

    # Install needed yum repositories
    echo "Performing installation step 140"
    # EOX
    rpm -Uvh --replacepkgs http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
    rpm --import /etc/pki/rpm-gpg/eox-package-maintainers.gpg
    if "$TESTING" ; then
        sed -e 's/^enabled=0/enabled=1/' -i /etc/yum.repos.d/eox-testing.repo
    fi

    echo "Performing installation step 150"
    # Set includepkgs in EOX Stable
    if ! grep -Fxq "includepkgs=gdal gdal-python gdal-libs EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1" /etc/yum.repos.d/eox.repo ; then
        sed -e 's/^\[eox\]$/&\nincludepkgs=gdal gdal-python gdal-libs EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/eox.repo
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

    echo "Performing installation step 160"
    # Set exclude in CentOS-Base
    if ! grep -Fxq "exclude=libxml2 libxml2-python libxerces-c-3_1" /etc/yum.repos.d/CentOS-Base.repo ; then
        sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
        sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
    fi

    echo "Performing installation step 170"
    # Re-install libxml2 from eox repository
    rpm -e --justdb --nodeps libxml2
    # Install packages
    yum install -y gdal gdal-python libxml2 libxml2-python mapserver mapserver-python EOxServer


    # allow installation of local RPMs if available
    if [ -f mapcache-*.rpm ] ; then
        echo "Installing local mapcache RPM `ls mapcache-*.rpm`"
        yum install -y mapcache-*.rpm
    else
        yum install -y mapcache
    fi
    if [ -f ngEO_Browse_Server-*.rpm ] ; then
        echo "Installing local ngEO_Browse_Server RPM `ls ngEO_Browse_Server-*.rpm`"
        yum install -y ngEO_Browse_Server-*.rpm
    else
        yum install -y ngEO_Browse_Server
    fi


    echo "Performing installation step 180"
    # Configure PostgreSQL/PostGIS database

    ## Write database configuration script
    TMPFILE=`mktemp`
    cat << EOF > "$TMPFILE"
#!/bin/sh -e
# cd to a "safe" location
cd /tmp
if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='template_postgis'")" != 1 ] ; then
    echo "Creating template database."
    createdb -E UTF8 template_postgis
    createlang plpgsql -d template_postgis
    psql postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
    if [ -f /usr/share/pgsql/contrib/postgis-64.sql ] ; then
        psql -d template_postgis -f /usr/share/pgsql/contrib/postgis-64.sql
    else
        psql -d template_postgis -f /usr/share/pgsql/contrib/postgis.sql
    fi
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

    echo "Performing installation step 190"
    # ngEO Browse Server
    [ -d "$NGEOB_INSTALL_DIR" ] || mkdir -p "$NGEOB_INSTALL_DIR"
    cd "$NGEOB_INSTALL_DIR"

    # Configure ngeo_browse_server_instance
    if [ ! -d ngeo_browse_server_instance ] ; then
        echo "Creating and configuring ngEO Browse Server instance."

        django-admin startproject --extension=conf --template=`python -c "import ngeo_browse_server, os; from os.path import dirname, abspath, join; print(join(dirname(abspath(ngeo_browse_server.__file__)), 'project_template'))"` ngeo_browse_server_instance

        echo "Performing installation step 200"
        cd -
        cd "${NGEOB_INSTALL_DIR}/ngeo_browse_server_instance"
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
        sed -e "s,http_service_url=http://localhost:8000/ows,http_service_url=$APACHE_NGEO_BROWSE_ALIAS/ows," -i ngeo_browse_server_instance/conf/eoxserver.conf
        MAPCACHE_DIR_ESCAPED=`echo $MAPCACHE_DIR | sed -e 's/\//\\\&/g'`
        sed -e "s/^tileset_root=$/tileset_root=$MAPCACHE_DIR_ESCAPED\//" -i ngeo_browse_server_instance/conf/ngeo.conf
        sed -e "s/^config_file=$/config_file=$MAPCACHE_DIR_ESCAPED\/$MAPCACHE_CONF/" -i ngeo_browse_server_instance/conf/ngeo.conf
        sed -e "s/^storage_dir=data\/storage$/storage_dir=$NGEOB_INSTALL_DIR_ESCAPED\/store/" -i ngeo_browse_server_instance/conf/ngeo.conf
        sed -e "s/^instance_id = $/instance_id = $NGEOB_INSTANCE_ID/" -i ngeo_browse_server_instance/conf/ngeo.conf

        # Configure logging
        if "$TESTING" ; then
            sed -e 's/DEBUG = False/DEBUG = True/' -i ngeo_browse_server_instance/settings.py
            sed -e 's/logging_level=INFO/#logging_level=INFO/' -i ngeo_browse_server_instance/conf/eoxserver.conf
        fi

        # Prepare DBs
        python manage.py syncdb --noinput
        python manage.py syncdb --database=mapcache --noinput
        python manage.py loaddata initial_rangetypes.json

        # Create admin user
        python manage.py createsuperuser --username=$DJANGO_USER --email=$DJANGO_MAIL --noinput
        python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ngeo_browse_server_instance.settings'); \
                   from django.contrib.auth.models import User;  admin = User.objects.get(username__exact='$DJANGO_USER'); \
                   admin.set_password('$DJANGO_PASSWORD'); admin.save();"

        # Collect static files
        python manage.py collectstatic --noinput

        # Make the instance read- and editable by apache
        chown -R apache:apache .

    else
        echo "Skipped installation steps 190 and 200"
    fi
    cd -

    echo "Performing installation step 210"
    # MapCache
    if [ ! -d "$MAPCACHE_DIR" ] ; then
        echo "Configuring MapCache."

        mkdir -p "$MAPCACHE_DIR"
        cd "$MAPCACHE_DIR"

        # Configure MapCache
        cat << EOF > "$MAPCACHE_DIR/$MAPCACHE_CONF"
<?xml version="1.0" encoding="UTF-8"?>
<mapcache>
    <auth_method name="cmdlineauth" type="cmd">
        <template>/usr/bin/python /usr/bin/request_authorization.py -b http://127.0.0.1:8000/webserver -u :user -l :tileset</template>
        <user_header>$MAPCACHE_USER_HEADER</user_header>
        <auth_cache type="memcache">
            <expires>1000</expires>
            <server>
                <host>localhost</host>
                <port>11211</port>
            </server>
        </auth_cache>
    </auth_method>

    <default_format>mixed</default_format>
    <format name="mypng" type="PNG">
        <compression>fast</compression>
    </format>
    <format name="myjpeg" type="JPEG">
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
        <format>mixed</format>
        <maxsize>4096</maxsize>
        <forwarding_rule name="wms">
            <param name="SERVICE" type="values">WMS</param>
            <http>
                <url>http://localhost/browse/ows</url>
            </http>
        </forwarding_rule>
    </service>
    <service type="wmts" enabled="true"/>

    <metadata>
        <title>ngEO Browse Server instance developed by EOX</title>
        <abstract>ngEO Browse Server instance developed by EOX</abstract>
        <keyword>KEYWORDLIST</keyword>
        <accessconstraints>UNKNOWN</accessconstraints>
        <fees>UNKNOWN</fees>
        <contactname>CONTACTPERSON</contactname>
        <contactphone>CONTACTVOICETELEPHONE</contactphone>
        <contactfacsimile>CONTACTFACSIMILETELEPHONE</contactfacsimile>
        <contactorganization>CONTACTORGANIZATION</contactorganization>
        <contactcity>CITY</contactcity>
        <contactstateorprovince>STATEORPROVINCE</contactstateorprovince>
        <contactpostcode>POSTCODE</contactpostcode>
        <contactcountry>COUNTRY</contactcountry>
        <contactelectronicmailaddress>CONTACTELECTRONICMAILADDRESS</contactelectronicmailaddress>
        <contactposition>CONTACTPOSITION</contactposition>
        <providername>CONTACTPERSON</providername>
        <providerurl>http://ngeo.eox.at</providerurl>
        <inspire_profile>true</inspire_profile>
        <inspire_metadataurl>METADATADATE</inspire_metadataurl>
        <defaultlanguage>eng</defaultlanguage>
        <language>eng</language>
    </metadata>

    <errors>empty_img</errors>
    <lock_dir>/tmp</lock_dir>
</mapcache>
EOF

        # Make the cache read- and editable by apache
        chown -R apache:apache .

        cd -
    else
        echo "Skipped installation step 210"
    fi

    echo "Performing installation step 220"
    # Shibboleth installation
    echo "Skipped installation step 220 as it was agreed that the authentication will always be done by a proxy."

    echo "Performing installation step 230"
    # Configure WebDAV
    if [ ! -d "$NGEOB_INSTALL_DIR/dav" ] ; then
        echo "Configuring WebDAV."
        mkdir -p "$NGEOB_INSTALL_DIR/dav"
        printf "$WEBDAV_USER:ngEO Browse Server:$WEBDAV_PASSWORD" | md5sum - > $NGEOB_INSTALL_DIR/dav/DavUsers
        sed -e "s/^\(.*\)  -$/test:ngEO Browse Server:\1/" -i $NGEOB_INSTALL_DIR/dav/DavUsers
        chown -R apache:apache "$NGEOB_INSTALL_DIR/dav"
        chmod 0640 "$NGEOB_INSTALL_DIR/dav/DavUsers"
        if [ ! -d "$NGEOB_INSTALL_DIR/store" ] ; then
            mkdir -p "$NGEOB_INSTALL_DIR/store"
            chown -R apache:apache "$NGEOB_INSTALL_DIR/store"
        fi
    else
        echo "Skipped installation step 230"
    fi

    echo "Performing installation step 240"
    # Add Apache configuration
    if [ ! -f "$APACHE_CONF" ] ; then
        echo "Configuring Apache."

        # Enable MapCache module
        if ! grep -Fxq "LoadModule mapcache_module modules/mod_mapcache.so" /etc/httpd/conf/httpd.conf ; then
            sed -e 's/^LoadModule version_module modules\/mod_version.so$/&\nLoadModule mapcache_module modules\/mod_mapcache.so/' -i /etc/httpd/conf/httpd.conf
        fi

        # Enable & configure Keepalive
        if ! grep -Fxq "KeepAlive On" /etc/httpd/conf/httpd.conf ; then
            sed -e 's/^KeepAlive .*$/KeepAlive On/' -i /etc/httpd/conf/httpd.conf
        fi
        if ! grep -Fxq "MaxKeepAliveRequests 0" /etc/httpd/conf/httpd.conf ; then
            sed -e 's/^MaxKeepAliveRequests .*$/MaxKeepAliveRequests 0/' -i /etc/httpd/conf/httpd.conf
        fi
        if ! grep -Fxq "KeepAliveTimeout 5" /etc/httpd/conf/httpd.conf ; then
            sed -e 's/^KeepAliveTimeout .*$/KeepAliveTimeout 5/' -i /etc/httpd/conf/httpd.conf
        fi

        echo "More performance tuning of apache is needed. Specifically the settings of the prefork module!"
        echo "A sample configuration could look like the following."
        cat << EOF
<IfModule prefork.c>
StartServers      64
MinSpareServers   32
MaxSpareServers   32
ServerLimit      380
MaxClients       380
MaxRequestsPerChild  0
</IfModule>
EOF

        # Configure WSGI module
        if ! grep -Fxq "WSGISocketPrefix run/wsgi" /etc/httpd/conf.d/wsgi.conf ; then
            echo "WSGISocketPrefix run/wsgi" >> /etc/httpd/conf.d/wsgi.conf
        fi

        # Add hostname
        HOSTNAME=`hostname`
        if ! grep -Gxq "127\.0\.0\.1.* $HOSTNAME" /etc/hosts ; then
            sed -e "s/^127\.0\.0\.1.*$/& $HOSTNAME/" -i /etc/hosts
        fi

        if [ ! -f "$APACHE_CONF.DISABLED" ] ; then
            cat << EOF > "$APACHE_CONF"
<VirtualHost *:80>
    ServerName $APACHE_ServerName
    ServerAdmin $APACHE_ServerAdmin

    DocumentRoot $NGEOB_INSTALL_DIR
    <Directory "$NGEOB_INSTALL_DIR">
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Order Allow,Deny
        Allow from all
    </Directory>

    Alias /static "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/static"
    Alias $APACHE_NGEO_BROWSE_ALIAS "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/wsgi.py"

    WSGIDaemonProcess ngeob processes=10 threads=1
    <Directory "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance">
        AllowOverride None
        Options -Indexes +ExecCGI -MultiViews +SymLinksIfOwnerMatch
        AddHandler wsgi-script .py
        WSGIProcessGroup ngeob
        Order Allow,Deny
        Allow from all
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

    MapCacheAlias $APACHE_NGEO_CACHE_ALIAS "$MAPCACHE_DIR/$MAPCACHE_CONF"
    <Directory $MAPCACHE_DIR>
        Options -Indexes
        Order Allow,Deny
        Allow from all
        Header set Access-Control-Allow-Origin *
    </Directory>

    ErrorLog "$NGEOB_LOG_DIR/httpd_error.log"
    ServerSignature Off
    LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\" %D \"%{$MAPCACHE_USER_HEADER}i\"" ngeo
    CustomLog "$NGEOB_LOG_DIR/httpd_access.log" ngeo
</VirtualHost>
EOF
        else
            echo "Found disabled Apache configuration -> enabling"
            mv "$APACHE_CONF.DISABLED" "$APACHE_CONF"
        fi

        if [ ! -f "$NGEOB_INSTALL_DIR/index.html" ] ; then
            # Add index.html to replace Apache HTTP server test page
            cat << EOF > "$NGEOB_INSTALL_DIR/index.html"
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html>
    <head>
        <title>ngEO Browse Server</title>
    </head>

    <body>
        <h1>ngEO Browse Server Test Page<br><font size="-1"><strong>powered by</font> <a href="http://eox.at">EOX</a></strong></h1>

        <p>This page is used to test the proper operation of the ngEO Browse Server after it has been installed. If you can read this page it means that the ngEO Browse Server installed at this site is working properly.</p>

        <p>Links to services:</p>
        <ul>
            <li>External <a href="/c/wmts/1.0.0/WMTSCapabilities.xml">WMTS</a> and <a href="/c?service=wms&request=GetCapabilities">WMS</a> interfaces</li>
            <li><a href="/browse">ngEO internal interfaces</a></li>
        </ul>
    </body>
</html>
EOF
        fi
    else
        echo "Skipped installation step 240"
    fi

    echo "Performing installation step 250"
    # start auth cache
    service memcached start

    # Reload Apache
    service httpd graceful

    echo "Performing installation step 260"
    # Configure Browse Server as service "ngeo"
    cp ngeo /etc/init.d/
    chkconfig --level 235 ngeo on
    chmod +x /etc/init.d/ngeo
    service ngeo start

    echo "Performing installation step 270"
    # Configure logrotate for ngeo log files
    if [ ! -d "$NGEO_REPORT_DIR" ] ; then
        mkdir -p "$NGEO_REPORT_DIR"
        chown -R apache:apache "$NGEO_REPORT_DIR"
    fi

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
        cd "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/"
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
        cd "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance/"
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

    echo "Finished $SUBSYSTEM installation"
    echo "Check successful installation by pointing your browse to the "
    echo "following URLs and check the correctness of the shown content:"
    echo "$NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/"
    echo "$NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/ows?service=wms&request=getcapabilities"
    echo "$NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/ingest"
    echo "$NGEOB_URL$APACHE_NGEO_CACHE_ALIAS/wmts?service=wmts&request=getcapabilities"
    echo "$NGEOB_URL$APACHE_NGEO_CACHE_ALIAS/?service=wms&request=getcapabilities"
    echo "$NGEOB_URL$APACHE_NGEO_STORE_ALIAS/ (log in using username password from above)"
    echo "Configure some browse layers."
    echo "Send some browse reports via POST to $NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/ingest and "
    echo "check successful ingestion by evaluating the response and "
    echo "consecutive WMTS and WMS requests to $NGEOB_URL$APACHE_NGEO_CACHE_ALIAS/wmts? and "
    echo "$NGEOB_URL$APACHE_NGEO_CACHE_ALIAS/?"

}

# ------------------------------------------------------------------------------
# Uninstall - Only remove software packages but keep instance
# ------------------------------------------------------------------------------
ngeo_uninstall() {

    if [ -f /etc/init.d/postgresql ] ; then
        chkconfig postgresql off
    fi

    echo "Performing uninstallation step 20"
    echo "Stop service ngeo"
    if [ -f /etc/init.d/ngeo ] ; then
        service ngeo stop

        echo "Delete service ngeo"
        rm -f /etc/init.d/ngeo
    fi

    echo "Performing uninstallation step 80"
    echo "If any of the data locations has been changed delete all browse data there."

    echo "Performing uninstallation step 90"
    echo "Delete extra Yum repositories"
    yum erase -y epel-release elgis-release eox-release

    echo "Performing uninstallation step 100"
    echo "Stop Apache HTTP server"
    if service httpd status ; then
        service httpd stop
    fi
    if [ -f /etc/init.d/httpd ] ; then
        chkconfig httpd off
    fi
    if [ -f "$APACHE_CONF" ] ; then
        echo "Disabling Apache VirtualHost configuration"
        mv "$APACHE_CONF" "$APACHE_CONF.DISABLED"
    fi

    echo "Stop memcached"#
    if service memcached status ; then
        service memcached stop
    fi
    if [ -f /etc/init.d/memcached ] ; then
        chkconfig memcached off
    fi

    echo "Performing uninstallation step 110"
    echo "Remove packages"
    yum erase -y  python-lxml mod_wsgi httpd pytz python-psycopg2 \
                  gdal gdal-python postgis mapserver Django14 mapserver-python \
                  mapcache ngEO_Browse_Server EOxServer libxerces-c-3_1 \
                  mod_ssl memcached

    echo "Finished $SUBSYSTEM uninstallation"
}

# ------------------------------------------------------------------------------
# Full Uninstall - Remove software and instance
# ------------------------------------------------------------------------------
ngeo_full_uninstall() {

    echo "------------------------------------------------------------------------------"
    echo " $SUBSYSTEM Full Uninstall"
    echo "------------------------------------------------------------------------------"

    echo "Performing uninstallation step 10"
    echo "Delete DB for ngEO Browse Server"

    echo "Stop Apache HTTP server"
    if service httpd status ; then
        service httpd stop
    fi

    if service postgresql status ; then
        ## Write database deletion script
        TMPFILE=`mktemp`
        cat << EOF > "$TMPFILE"
#!/bin/sh -e
# cd to a "safe" location
cd /tmp
if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")" == 1 ] ; then
    echo "Deleting ngEO Browse Server database."
    dropdb $DB_NAME
fi
if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")" == 1 ] ; then
    echo "Deleting ngEO database user."
    dropuser $DB_USER
fi


if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='template_postgis'")" == 1 ] ; then
    echo "Deleting template database."
    psql postgres -c "UPDATE pg_database SET datistemplate='false' WHERE datname='template_postgis';"
    dropdb template_postgis
fi
EOF
## End of database deletion script

        if [ -f $TMPFILE ] ; then
            chgrp postgres $TMPFILE
            chmod g+rx $TMPFILE
            su postgres -c "$TMPFILE"
            rm "$TMPFILE"
        else
            echo "Script to delete DB not found."
        fi
        service postgresql stop
    else
        echo "DB not deleted because PostgreSQL server is not running"
    fi

    echo "Performing uninstallation step 30"
    echo "Delete ngEO Browse Server instance"
    rm -rf "${NGEOB_INSTALL_DIR}/ngeo_browse_server_instance" "${NGEOB_INSTALL_DIR}/index.html"

    echo "Performing uninstallation steps 40 and 50"
    echo "Delete MapCache instance and configuration including authorization"
    rm -rf "${MAPCACHE_DIR}"

    echo "Performing uninstallation step 60"
    echo "Delete WebDAV"
    rm -rf "${NGEOB_INSTALL_DIR}/dav"
    rm -rf "${NGEOB_INSTALL_DIR}/store"
    if [ -d "${NGEOB_INSTALL_DIR}" ] ; then
        rmdir "${NGEOB_INSTALL_DIR}"
    fi

    echo "Performing uninstallation step 70"
    echo "Delete Apache HTTP server configuration"
    rm -rf "${APACHE_CONF}" "${APACHE_CONF}.DISABLED"

    # remove packages
    ngeo_uninstall

    yum erase -y postgresql

}


# ------------------------------------------------------------------------------
# Status (check status of a specific RPM)
# ------------------------------------------------------------------------------
ngeo_check_rpm_status () {
    if [ -n "`rpm -qa | grep $1`" ] ; then
        echo -e "$1: \033[1;32minstalled\033[m\017"
    else
        echo -e "$1: \033[1;31mmissing\033[m\017"
    fi
}


# ------------------------------------------------------------------------------
# Status
# ------------------------------------------------------------------------------
ngeo_status() {
    echo "------------------------------------------------------------------------------"
    echo " $SUBSYSTEM status check"
    echo "------------------------------------------------------------------------------"
    ngeo_check_rpm_status ngEO_Browse_Server
    ngeo_check_rpm_status EOxServer
    ngeo_check_rpm_status mapcache
}


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
case "$1" in
install)
    ngeo_install
;;
uninstall)
    ngeo_uninstall
;;
full_uninstall)
    ngeo_full_uninstall
;;
status)
    ngeo_status
;;
*)
    echo "Usage: $0 {install|uninstall|full_uninstall|status}"
exit 1
;;
esac

# END ########################################################################
