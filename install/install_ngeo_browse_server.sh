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
# - Uninstallation: sudo ./ngeo-install.sh uninstall
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

# Shibboleth
USE_SHIBBOLETH=true

IDP_HOST="um-sso-idp.gmv.com"
IDP_PORT="443"
IDP_SOAP="8888"
IDP_ENTITYID="https://um-sso-idp.gmv.com:443/shibboleth"
IDP_CERT_FILE="/etc/shibboleth/umsso.pem"

SP_NAME="brow"
SP_ENTITYID="https://5.9.173.39/shibboleth"
SP_HOST="5.9.173.39"
SP_PORT="443"
SP_ORG_DISP_NAME="ngEO Browse Server"
SP_CONTACT="webmaster@eox.at"
SP_CERT_FILE="/etc/shibboleth/brow-spcert.pem"
SP_CERT_FILE_2="/etc/pki/tls/certs/brow-spcert.pem"
SP_KEY_FILE="/etc/shibboleth/brow-spkey.pem"
SP_KEY_FILE_2="/etc/pki/tls/private/brow-spkey.pem"

SP_PROTECTED_FULL_URL="https://5.9.173.39"
SP_HOME_FULL_URL="https://5.9.173.39"
SP_HOME_BASE_URL="https://5.9.173.39"

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
    yum install -y python-lxml mod_wsgi httpd memcached postgresql-server python-psycopg2 pytz

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
    rpm -Uvh --replacepkgs http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
    echo "Performing installation step 100"
    # ELGIS
    rpm -Uvh --replacepkgs http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

    echo "Performing installation step 110"
    # Apply available upgrades
    yum update -y

    echo "Performing installation step 120"
    # Install packages
    yum install -y gdal gdal-python postgis Django14 proj-epsg


    #------------------------
    # Component installation
    #------------------------

    echo "Assuming successful execution of installation step 130"

    # Install needed yum repositories
    echo "Performing installation step 140"
    # EOX
    rpm -Uvh --replacepkgs http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
    if "$TESTING" ; then
        sed -e 's/^enabled=0/enabled=1/' -i /etc/yum.repos.d/eox-testing.repo
    fi

    echo "Performing installation step 150"
    # Set includepkgs in EOX Stable
    if ! grep -Fxq "includepkgs=EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1" /etc/yum.repos.d/eox.repo ; then
        sed -e 's/^\[eox\]$/&\nincludepkgs=EOxServer mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/eox.repo
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
    if ! grep -Fxq "exclude=libxml2 libxml2-python" /etc/yum.repos.d/CentOS-Base.repo ; then
        sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
        sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
    fi

    echo "Performing installation step 170"
    # Install packages
    yum install -y libxml2 libxml2-python mapserver mapserver-python \
                   mapcache ngEO_Browse_Server EOxServer

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
        sed -e "s,http_service_url=http://localhost:8000/ows,http_service_url=$NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/ows," -i ngeo_browse_server_instance/conf/eoxserver.conf
        MAPCACHE_DIR_ESCAPED=`echo $MAPCACHE_DIR | sed -e 's/\//\\\&/g'`
        sed -e "s/^tileset_root=$/tileset_root=$MAPCACHE_DIR_ESCAPED\//" -i ngeo_browse_server_instance/conf/ngeo.conf
        sed -e "s/^config_file=$/config_file=$MAPCACHE_DIR_ESCAPED\/$MAPCACHE_CONF/" -i ngeo_browse_server_instance/conf/ngeo.conf
        sed -e "s/^storage_dir=data\/storage$/storage_dir=$NGEOB_INSTALL_DIR_ESCAPED\/store/" -i ngeo_browse_server_instance/conf/ngeo.conf
        
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

        cd -
    else
        echo "Skipped installation steps 190 and 200"
    fi

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
        <user_header>user</user_header>
        <auth_cache type="memcache">
            <expires>1000</expires>
            <server>
                <host>localhost</host>
                <port>11211</port>
            </server>
        </auth_cache>
    </auth_method>
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
        <format>mixed</format>
        <maxsize>4096</maxsize>
    </service>
    <service type="wmts" enabled="true"/>

    <errors>empty_img</errors>
    <lock_dir>/tmp</lock_dir>
EOF

        if "$TESTING" ; then
            cat << EOF >> "$MAPCACHE_DIR/$MAPCACHE_CONF"

    <service type="demo" enabled="true"/>
</mapcache>
EOF
        else
            cat << EOF >> "$MAPCACHE_DIR/$MAPCACHE_CONF"
</mapcache>
EOF
        fi

        # Make the cache read- and editable by apache
        chown -R apache:apache .

        cd -
    else
        echo "Skipped installation step 210"
    fi

    echo "Performing installation step 220"
    # Shibboleth installation
    if "$USE_SHIBBOLETH" ; then
        echo "Installing Shibboleth"

        # add the shibboleth rpm repository
        cd /etc/yum.repos.d/
        wget http://download.opensuse.org/repositories/security://shibboleth/CentOS_CentOS-6/security:shibboleth.repo
        cd -

        # Set exclude in security:shibboleth.repo
        if ! grep -Fxq "exclude=libxerces-c-3_1" /etc/yum.repos.d/CentOS-Base.repo ; then
            sed -e 's/^\[security_shibboleth\]$/&\nexclude=libxerces-c-3_1/' -i /etc/yum.repos.d/security:shibboleth.repo
        fi

        # TODO includepkg / excludepkg 
        yum install -y libxerces-c-3_1 shibboleth mod_ssl
        
        # TODO what is this?
        rm -f /etc/shibboleth/attribute-policy.xml /etc/shibboleth/attribute-map.xml /etc/shibboleth/shibboleth2.xml

        # sample keys & certs provided by sso_checkpoint.tgz
        # TODO: test if files exist and DON'T overwrite them
        echo "Adding certificates"
        cat << EOF > "$IDP_CERT_FILE"
-----BEGIN CERTIFICATE-----
MIIDaDCCAlACCQD407UfBsOwkTANBgkqhkiG9w0BAQUFADB2MQswCQYDVQQGEwJT
UDEPMA0GA1UECBMGTWFkcmlkMQ8wDQYDVQQHEwZNYWRyaWQxDDAKBgNVBAoTA0dN
VjEMMAoGA1UECxMDR01WMQ0wCwYDVQQDEwRibmNjMRowGAYJKoZIhvcNAQkBFgti
bmNjQGdtdi5lczAeFw0xMzA2MDMxMTQwNDBaFw0xNDA2MDMxMTQwNDBaMHYxCzAJ
BgNVBAYTAlNQMQ8wDQYDVQQIEwZNYWRyaWQxDzANBgNVBAcTBk1hZHJpZDEMMAoG
A1UEChMDR01WMQwwCgYDVQQLEwNHTVYxDTALBgNVBAMTBGJuY2MxGjAYBgkqhkiG
9w0BCQEWC2JuY2NAZ212LmVzMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC
AQEAom6d/dKq+wRHgYlRt9717QUrL1477GiNOmFGMsZjgqe6b16xwK3WiLZ0vT3c
EY6ix/NtghTkF+MK4Vf50aiO4gpAy49sX/gb1cjDM7BezvAnv5JRnhFRPPAoPwyT
o4+nsS7nLfkoz4ERw1OYP06UrqOujgQnZmO6m4LsQueTOn2V51s3YMaf10TZKIa4
goVHmbaLqYoKGmUqR+jig5/Ay/0tQvBmKh46BKQ4Lz+vzyty92AyquOkkSvhlg2W
BI1fJ1Llvqd/1l1ybOmYKMJyI33NRAcdZ2cYwSr9VRueR++1w8oxqvxL8wuhglbo
p479AQcyxa8EFO4vlp46NoPyHwIDAQABMA0GCSqGSIb3DQEBBQUAA4IBAQAx/vgK
ocGFJ0haiyAgX/eUXNbVw4khmPrOY7NnB0CM1C4LRx8TtLcWUFWERaB+rN0kcZpq
m04zHtEwzgaB5UlWuIKDDrOCFb65XIHqTdA/OaRzHBr2nHcs1dAQ0MCJImrCIs7j
7OfXnHI0SJTLhUdbaE2bdXbia8tXHu1LYMulrCRdwgTdQ4ve50gmYs5FW6fTYm65
XL3TPYMasiJpLzLnhmrXe2mGUczESsQtvs7YN7PeddZ9L1NiU1GNKynmb8R3QniS
fp/4TbFjgBpOYINLiMrHYbjfwBbaG8VivDyHRKvh5vo6e/Dhh6HgQEYkevQeZ2K1
E3Lv9dEVxjoAjCd4
-----END CERTIFICATE-----
EOF

        cat << EOF > "$SP_CERT_FILE"
-----BEGIN CERTIFICATE-----
MIIDUzCCAjugAwIBAgIBAjANBgkqhkiG9w0BAQUFADCBmDEqMCgGCSqGSIb3DQEJ
ARYbYWRtaW5AdW0tc3NvLWlkcC5lby5lc2EuaW50MQswCQYDVQQGEwJJVDEOMAwG
A1UECBMFSXRhbHkxDjAMBgNVBAcTBUVzcmluMQwwCgYDVQQKEwNFU0ExDzANBgNV
BAsTBkVTQSBDQTEeMBwGA1UEAxMVdW0tc3NvLWlkcC5lby5lc2EuaW50MB4XDTEz
MDYyODE2MDQzOFoXDTIzMDYyNjE2MDQzOFowQTELMAkGA1UEBhMCSVQxDDAKBgNV
BAoTA0VTQTELMAkGA1UECxMCRU8xFzAVBgNVBAMTDmJyb3cubm92YWxvY2FsMIIB
IjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0EMb78IAIVzrPYfPZ05x58NK
TJjZuVcXRsksdCzHb8bH7OBJeeB+LYaCC0rxeCIS240ih9r6IZ2wtV20lC63SNiR
LRniydXprMPxZnu91c5xDmCA35oIcAN9l4/uZ9HYGoAx+p8bpGBsnR8IlABHLkYR
iHQ2+9V3Atj+TMllcVtPrLfRHBE0o4mkzsWfCOCnZECK4HavfiUQiZhLTx4x2lVD
92Yi2kSGWeNmvkBLJcdboQkGCi49mkYptzhFnjCp0lOxP9H5ebsNf8XNrg1Eyx7Y
8MCiZsiO8klr/OSHyKINos+Vak/OQ727C2U4UtvL/0+y3rOzj36PnZVG0YR7XQID
AQABMA0GCSqGSIb3DQEBBQUAA4IBAQAmgG3St2Hq4g9/qYS2HjwWKFVKS+D6xTkM
dI7y+ckrv5drhtV25pKiDkB10z8puxkvMjeENLTVrS8PEEM+9+BOFJxTNqIrhjNt
yw21CCha4X5Nr/Dsgtb6SfZ1FoNay3iGACaiLv+YVBCK0gxZtEHW+9QlqfeCqBnC
GsRw1EDSvWcW7SutkGe/ciU+JqIhx9WA1Uw/6+cOwgIzeVRgGqpRqxHjeI8kBFp1
5SiFeNW8qjZQ3cuUeLqNGnWWlhOKSlgYgAU7xahQKyxOwjTkENrpR1q/MvHxJ3as
CVrb+DBUsK7hT021nelfgqIahov5mr4gq4F4m0KuoLOB8c3FZOA5
-----END CERTIFICATE-----
EOF

        cat << EOF > "$SP_CERT_FILE_2"
`cat $SP_CERT_FILE`
EOF

        cat << EOF > "$SP_KEY_FILE"
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0EMb78IAIVzrPYfPZ05x58NKTJjZuVcXRsksdCzHb8bH7OBJ
eeB+LYaCC0rxeCIS240ih9r6IZ2wtV20lC63SNiRLRniydXprMPxZnu91c5xDmCA
35oIcAN9l4/uZ9HYGoAx+p8bpGBsnR8IlABHLkYRiHQ2+9V3Atj+TMllcVtPrLfR
HBE0o4mkzsWfCOCnZECK4HavfiUQiZhLTx4x2lVD92Yi2kSGWeNmvkBLJcdboQkG
Ci49mkYptzhFnjCp0lOxP9H5ebsNf8XNrg1Eyx7Y8MCiZsiO8klr/OSHyKINos+V
ak/OQ727C2U4UtvL/0+y3rOzj36PnZVG0YR7XQIDAQABAoIBAHnDUtkaFxNqjUs7
VUL0NVqo7o7cKyfWyJAlXK1L5QrwMMHI3Iy6eWtKokvR9F4lpdrhqJe/qtDurntL
nyGoMpcPr8mrwdH6FJZjNYeSv4n7GlSqjY6uM1KyZ8Kub1gZ83yDCTWbwwCXM8ml
dFF73CIs62FZeTBCPUPX9M6WTY45IuuQx8sz2v8YduzFvmOVcCzGiNIF5endZoGk
WaN72iVaSn5zjOr7VsmtDvNSDKTARF00GgKjHk49szYlklEqmXxb6b/E0M8X3FWd
7XZaXXR4ElvkW7LTmHaKR9FVmnNEPVLdRjWjW5X3tY0CAy5hYMSD/5M+SGIbtsPW
YSohEMECgYEA+u0BmW6x8111ZzSfL6/ZYGJtSm18gTGpus4cK6GfHc7wvm2w09Wj
SrAhgVqA74aBCzLzi3iskU0yMQpQOsMjN1bqT7PNiGMdgW45LD1B2BLvzJxEAqRS
afyR+U8ajqp+XIOCtMnB0cIGecEC6jCEHiZzcO1hu7WvqC9tIT91mE0CgYEA1Hk9
0JnpkOEk/XLVgyX8ZTzaz4+4pXOCveP64ezj4O7C3dgGHTvM+c6toMkWJwQ2o7hh
oqMA5SQ8gmMujT0+zYhRHwgulRLKEuj//HEtNe3GrwkIQw7Z8CoxFPIMCY+REHlu
Xo2i+hYB+tH0CfiKsDg4rT8OSoHB206dRfNR91ECgYEAt8+2RDcalDP6NMgPdFdU
3Y48kTDy65D9zKH/cNbMQIG/SUABMKxnGec8JA2wNcZJ8XI5hgm4IBh0lAgCDYm0
2m0I56nG/gndK1sa9pVJDoeQskomZ+kHliw2onKX+bpbJloP/W9uU8HWDIqfH/66
SXvRRQAff+nv6zwSrTBXbGECgYBfgrC62LUZn1uVYs1/ys+OYrCppR2HokkfOyBH
9sjpD+sg9j6pXXxivvll0X7Xwxkct4GMLmH0nzlkE1mVu/ZDRgfRP0hRUsTrgzmv
LOD54QzzGchQ/JgTUaQGmle25IZ9NVjbwCeG6+Wv7jkZUlRlqqAvoKy36WRPRSOF
kj9CQQKBgHPdX5Fa8PXTcsbeEnxiMqj9ZGlpwgsC1X2WFnHfkPLdMMnRh6QRtGfU
0hk/L4tak/FpxVNa8QITldpWH4xc1/ccT99BYChMDeFj2a70AoR9dMkHedmD6399
CGmeL8PBsysX+OfUcxFs3NkR7dZ5KdWXz12Q4o6iGYXGhpenr8TC
-----END RSA PRIVATE KEY-----
EOF

        cat << EOF > "$SP_KEY_FILE_2"
`cat $SP_KEY_FILE`
EOF


        # Read certificates and keys into variables
        IDP_CERT_CONTENT=`cat $IDP_CERT_FILE | grep -v CERTIFICATE`
        SP_CERT_CONTENT=`cat $SP_CERT_FILE | grep -v CERTIFICATE`
        SP_KEY_CONTENT=`cat $SP_KEY_FILE | grep -v PRIVATE`

        echo "Configuring Shibboleth"

        # attribute-map.xml
        cat << EOF > /etc/shibboleth/attribute-map.xml
<Attributes xmlns="urn:mace:shibboleth:2.0:attribute-map" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Attribute name="urn:mace:dir:attribute-def:cn" id="Umsso-Person-commonName" />
    <Attribute name="urn:mace:dir:attribute-def:spid$SP_NAME" id="SP-Person-Identifier" />
    <Attribute name="urn:mace:dir:attribute-def:mail" id="Umsso-Person-Email" />
</Attributes>
EOF

        # attribute-policy.xml
        cat << EOF > /etc/shibboleth/attribute-policy.xml
<afp:AttributeFilterPolicyGroup
    xmlns="urn:mace:shibboleth:2.0:afp:mf:basic" xmlns:basic="urn:mace:shibboleth:2.0:afp:mf:basic" xmlns:afp="urn:mace:shibboleth:2.0:afp" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <afp:AttributeFilterPolicy>
        <afp:PolicyRequirementRule xsi:type="ANY"/>
        <afp:AttributeRule attributeID="*">
            <afp:PermitValueRule xsi:type="ANY"/>
        </afp:AttributeRule>
    </afp:AttributeFilterPolicy>
</afp:AttributeFilterPolicyGroup>
EOF

        # idp-metadata.xml
        cat << EOF > /etc/shibboleth/idp-metadata.xml
<EntityDescriptor entityID="$IDP_ENTITYID" validUntil="2030-01-01T00:00:00Z"
                  xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
                  xmlns:shibmd="urn:mace:shibboleth:metadata:1.0"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <IDPSSODescriptor protocolSupportEnumeration="urn:mace:shibboleth:1.0 urn:oasis:names:tc:SAML:1.1:protocol urn:oasis:names:tc:SAML:2.0:protocol">

        <Extensions>
            <shibmd:Scope regexp="false">gmv.com</shibmd:Scope>
        </Extensions>

        <KeyDescriptor>
            <ds:KeyInfo>
                <ds:X509Data>
                    <ds:X509Certificate>
$IDP_CERT_CONTENT
                    </ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </KeyDescriptor>

        <ArtifactResolutionService Binding="urn:oasis:names:tc:SAML:1.0:bindings:SOAP-binding" Location="https://$IDP_HOST:$IDP_SOAP/idp/profile/SAML1/SOAP/ArtifactResolution" index="1"/>

        <ArtifactResolutionService Binding="urn:oasis:names:tc:SAML:2.0:bindings:SOAP" Location="https://$IDP_HOST:$IDP_SOAP/idp/profile/SAML2/SOAP/ArtifactResolution" index="2"/>

        <NameIDFormat>urn:mace:shibboleth:1.0:nameIdentifier</NameIDFormat>
        <NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:transient</NameIDFormat>

        <SingleSignOnService Binding="urn:mace:shibboleth:1.0:profiles:AuthnRequest" Location="https://$IDP_HOST:$IDP_PORT/idp/profile/Shibboleth/SSO" />

        <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="https://$IDP_HOST:$IDP_PORT/idp/profile/SAML2/Redirect/SSO" />

        <SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="https://$IDP_HOST:$IDP_PORT/idp/profile/SAML2/Redirect/SLO" ResponseLocation="https://$IDP_HOST:$IDP_PORT/idp/profile/SAML2/Redirect/SLO"/>
    </IDPSSODescriptor>

    <AttributeAuthorityDescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:1.1:protocol urn:oasis:names:tc:SAML:2.0:protocol">

        <Extensions>
            <shibmd:Scope regexp="false">esa.int</shibmd:Scope>
        </Extensions>

        <KeyDescriptor>
            <ds:KeyInfo>
                <ds:X509Data>
                    <ds:X509Certificate>
$IDP_CERT_CONTENT
                    </ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </KeyDescriptor>

        <AttributeService Binding="urn:oasis:names:tc:SAML:1.0:bindings:SOAP-binding" Location="https://$IDP_HOST:$IDP_SOAP/idp/profile/SAML1/SOAP/AttributeQuery" />

        <AttributeService Binding="urn:oasis:names:tc:SAML:2.0:bindings:SOAP" Location="https://$IDP_HOST:$IDP_SOAP/idp/profile/SAML2/SOAP/AttributeQuery" />        

        <NameIDFormat>urn:mace:shibboleth:1.0:nameIdentifier</NameIDFormat>
        <NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:transient</NameIDFormat>
    </AttributeAuthorityDescriptor>
</EntityDescriptor>
EOF

        # shibboleth2.xml
        cat << EOF > /etc/shibboleth/shibboleth2.xml
<SPConfig xmlns="urn:mace:shibboleth:2.0:native:sp:config"
          xmlns:conf="urn:mace:shibboleth:2.0:native:sp:config"
          xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
          xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
          xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
          logger="/etc/shibboleth/shibd.logger" clockSkew="7600">

    <!-- The OutOfProcess section contains properties affecting the shibd daemon. -->
    <OutOfProcess logger="/etc/shibboleth/shibd.logger"></OutOfProcess>

    <!-- The InProcess section contains settings affecting web server modules/filters. -->
    <InProcess logger="/etc/shibboleth/native.logger"></InProcess>

    <!-- Only one listener can be defined, to connect in-process modules to shibd. -->
    <UnixListener address="/var/run/shibboleth/shibd.sock" />

    <!--<TCPListener address="127.0.0.1" port="12345" acl="127.0.0.1"/> -->
    <!-- This set of components stores sessions and other persistent data in daemon memory. -->
    <StorageService type="Memory" id="mem" cleanupInterval="900" />
    <SessionCache type="StorageService" StorageService="mem" cacheTimeout="3600" inprocTimeout="900" cleanupInterval="900" />
    <ReplayCache StorageService="mem" />
    <ArtifactMap artifactTTL="180" />

    <!-- To customize behavior, map hostnames and path components to applicationId and other settings. -->
    <RequestMapper type="Native">
        <RequestMap applicationId="default">
            <Host scheme="https" name="$SP_HOST" port="$SP_PORT" authType="shibboleth" requireSession="true" exportAssertion="true" />
        </RequestMap>
    </RequestMapper>


    <ApplicationDefaults id="default" policyId="default" entityID="$SP_ENTITYID" homeURL="$SP_PROTECTED_FULL_URL" REMOTE_USER="eppn persistent-id targeted-id" signing="false" encryption="false" timeout="30" connectTimeout="15">

        <Sessions exportLocation="/GetAssertion" lifetime="7200" timeout="3600" checkAddress="false" consistentAddress="true" handlerURL="/Shibboleth.sso" handlerSSL="true" idpHistory="true" cookieProps="https" idpHistoryDays="7">
            <SessionInitiator type="SAML2" entityID="$IDP_ENTITYID" forceAuthn="false" Location="/Login" template="/etc/shibboleth/bindingTemplate.html"/>
            <md:AssertionConsumerService Location="/SAML2/Artifact" index="1" Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact" />
            <md:SingleLogoutService Location="/SLO/Redirect" Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" conf:template="/etc/shibboleth/bindingTemplate.html" />
            <LogoutInitiator type="Local" Location="/Logout" template="/etc/shibboleth/bindingTemplate.html" />
            <LogoutInitiator type="SAML2" Location="/SLogout" template="/etc/shibboleth/bindingTemplate.html" />
        </Sessions>

        <Errors session="/etc/shibboleth/sessionError.html" metadata="/etc/shibboleth/metadataError.html" access="/etc/shibboleth/accessError.html" ssl="/etc/shibboleth/sslError.html" supportContact="$SP_CONTACT" logoLocation="/shibboleth-sp/logo.jpg" styleSheet="/shibboleth-sp/main.css" globalLogout="/etc/shibboleth/globalLogout.html" localLogout="/etc/shibboleth/localLogout.html"></Errors>

        <RelyingParty Name="$IDP_ENTITYID" keyName="defcreds"/>

        <MetadataProvider type="Chaining">
            <MetadataProvider type="XML" file="/etc/shibboleth/idp-metadata.xml"/>
            <MetadataProvider type="XML" file="/etc/shibboleth/brow-metadata.xml"/>
        </MetadataProvider>

        <!-- Chain the two built-in trust engines together. -->
        <TrustEngine type="Chaining">
            <TrustEngine type="ExplicitKey"/>
            <TrustEngine type="PKIX"/>
        </TrustEngine>

        <!-- Map to extract attributes from SAML assertions. -->
        <AttributeExtractor type="XML" path="/etc/shibboleth/attribute-map.xml"/>

        <!-- Use a SAML query if no attributes are supplied during SSO. -->
        <AttributeResolver type="Query"/>

        <!-- Default filtering policy for recognized attributes, lets other data pass. -->
        <AttributeFilter type="XML" path="/etc/shibboleth/attribute-policy.xml"/>

        <CredentialResolver type="File" key="$SP_KEY_FILE" certificate="$SP_CERT_FILE" keyName="defcreds"/>
    </ApplicationDefaults>

    <!-- Each policy defines a set of rules to use to secure messages. -->
    <SecurityPolicies>
        <Policy id="default" validate="false">
            <PolicyRule type="MessageFlow" checkReplay="true" expires="60"/>
            <PolicyRule type="Conditions">
                <PolicyRule type="Audience"/>
            </PolicyRule>
            <PolicyRule type="ClientCertAuth" errorFatal="true"/>
            <PolicyRule type="XMLSigning" errorFatal="true"/>
            <PolicyRule type="SimpleSigning" errorFatal="true"/>
        </Policy>
    </SecurityPolicies>

</SPConfig>
EOF

        # brow-metadata.xml
        cat << EOF > /etc/shibboleth/brow-metadata.xml
<EntityDescriptor entityID="$SP_ENTITYID" validUntil="2030-01-01T00:00:00Z"
                  xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
                  xmlns:shibmd="urn:mace:shibboleth:metadata:1.0"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <KeyDescriptor>
            <ds:KeyInfo>
                <ds:X509Data>
                    <ds:X509Certificate>
$SP_CERT_CONTENT
                    </ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </KeyDescriptor>

        <AssertionConsumerService Location="$SP_HOME_BASE_URL/Shibboleth.sso/SAML2/Artifact" index="1" isDefault="true" 
          Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"/>

        <SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="$SP_HOME_BASE_URL/Shibboleth.sso/SLO/Redirect"/>

        <NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:transient</NameIDFormat>
    </SPSSODescriptor>

    <Organization>
        <OrganizationName xml:lang="en">$SP_NAME</OrganizationName>
        <OrganizationDisplayName xml:lang="en">$SP_ORG_DISP_NAME</OrganizationDisplayName>
        <OrganizationURL xml:lang="en">$SP_HOME_FULL_URL</OrganizationURL>
    </Organization>
</EntityDescriptor>
EOF

        # Setup Certificates

        # Restart the shibboleth daemon
        service shibd restart

        # mod_shib configuration
        cat << EOF > /etc/httpd/conf.d/shib.conf
# https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPApacheConfig

# RPM installations on platforms with a conf.d directory will
# result in this file being copied into that directory for you
# and preserved across upgrades.

# For non-RPM installs, you should copy the relevant contents of
# this file to a configuration location you control.

#
# Load the Shibboleth module.
#
LoadModule mod_shib /usr/lib64/shibboleth/mod_shib_22.so

#
# Ensures handler will be accessible.
#
<Location /Shibboleth.sso>
  Satisfy Any
  Allow from all
</Location>

#
# Used for example style sheet in error templates.
#
<IfModule mod_alias.c>
  <Location /shibboleth-sp>
    Satisfy Any
    Allow from all
  </Location>
  Alias /shibboleth-sp/main.css /usr/share/shibboleth/main.css
</IfModule>

#
# Configure the module for content.
#
# You MUST enable AuthType shibboleth for the module to process
# any requests, and there MUST be a require command as well. To
# enable Shibboleth but not specify any session/access requirements
# use "require shibboleth".
#
<Location /secure>
  AuthType shibboleth
  ShibRequestSetting requireSession 1
  require valid-user
</Location>
EOF

        echo "Done installing Shibboleth"

    else
        echo "Skipped installation step 220"
    fi
    # END Shibboleth Installation

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

        cat << EOF > "$APACHE_CONF"
<VirtualHost *:80>
    ServerName $APACHE_ServerName
    ServerAdmin $APACHE_ServerAdmin

    DocumentRoot $NGEOB_INSTALL_DIR
    <Directory "$NGEOB_INSTALL_DIR">
        Options Indexes FollowSymLinks
        AllowOverride None
        Order Deny,Allow
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
EOF

        # If shibboleth is not installation enable MapCache via http
        if ! "$USE_SHIBBOLETH" ; then
            cat << EOF >> "$APACHE_CONF"
    MapCacheAlias $APACHE_NGEO_CACHE_ALIAS "$MAPCACHE_DIR/$MAPCACHE_CONF"
    <Directory $MAPCACHE_DIR>
        Order Allow,Deny
        Allow from all
        Header set Access-Control-Allow-Origin *
    </Directory>
</VirtualHost>
EOF
        # If shibboleth is installation enable MapCache via https
        else
            # Disable default ssl.conf
            mv /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf_DISABLED

            cat << EOF >> "$APACHE_CONF"
</VirtualHost>


LoadModule ssl_module modules/mod_ssl.so
Listen $SP_PORT

SSLPassPhraseDialog  builtin
SSLSessionCache         shmcb:/var/cache/mod_ssl/scache(512000)
SSLSessionCacheTimeout  300
SSLMutex default
SSLRandomSeed startup file:/dev/urandom  256
SSLRandomSeed connect builtin
SSLCryptoDevice builtin

<VirtualHost _default_:$SP_PORT>
    ServerName $SP_NAME.novalocal
    ServerAdmin $APACHE_ServerAdmin

    ErrorLog logs/ssl_error_log
    TransferLog logs/ssl_access_log
    LogLevel warn

    SSLEngine on
    SSLProtocol all -SSLv2
    SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW
    SSLCertificateFile /etc/pki/tls/certs/brow-spcert.pem
    SSLCertificateKeyFile /etc/pki/tls/private/brow-spkey.pem
    SSLOptions +StdEnvVars +ExportCertData +OptRenegotiate
    RequestHeader set SSL_CLIENT_CERT "%{SSL_CLIENT_CERT}s"
    SSLVerifyDepth 2

    SetEnvIf User-Agent ".*MSIE.*" \
             nokeepalive ssl-unclean-shutdown \
             downgrade-1.0 force-response-1.0

    DocumentRoot $NGEOB_INSTALL_DIR
    <Directory "$NGEOB_INSTALL_DIR">
        Options Indexes FollowSymLinks
        AllowOverride None
        Order Deny,Allow
        Deny from all
        AuthType shibboleth
        Require shibboleth
        ShibUseHeaders On
    </Directory>

    MapCacheAlias $APACHE_NGEO_CACHE_ALIAS "$MAPCACHE_DIR/$MAPCACHE_CONF"
    <Directory $MAPCACHE_DIR>
        Order Allow,Deny
        Allow from all
        Header set Access-Control-Allow-Origin *
        AuthType shibboleth
        Require shibboleth
        ShibUseHeaders On
    </Directory>
</VirtualHost>
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
    echo "Stop Apache HTTP server"#
    if service httpd status ; then
        service httpd stop
    fi
    if [ -f /etc/init.d/httpd ] ; then
        chkconfig httpd off
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
                  shibboleth mod_ssl memcached

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
    rm -rf "${NGEOB_INSTALL_DIR}/ngeo_browse_server_instance"

    echo "Performing uninstallation step 40"
    echo "Delete MapCache instance"
    rm -rf "${MAPCACHE_DIR}"

    echo "Performing uninstallation step 50"
    echo "Delete Authorization module configuration"
    # TODO V2

    echo "Performing uninstallation step 60"
    echo "Delete WebDAV"
    rm -rf "${NGEOB_INSTALL_DIR}/dav"
    rm -rf "${NGEOB_INSTALL_DIR}/store"
    if [ -d "${NGEOB_INSTALL_DIR}" ] ; then
        rmdir "${NGEOB_INSTALL_DIR}"
    fi

    echo "Performing uninstallation step 70"
    echo "Delete Apache HTTP server configuration"
    rm -rf "${APACHE_CONF}"

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
    echo "Usage: $0 {install|uninstall|status}"
exit 1
;;
esac

# END ########################################################################
