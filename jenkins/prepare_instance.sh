#!/bin/sh -xe

# ngEO Browse Server
NGEOB_INSTALL_DIR="$WORKSPACE"
NGEOB_URL="http://ngeo.eox.at"

# PostgreSQL/PostGIS database
DB_NAME="ngeo_browse_server_db"
DB_USER="jenkins"
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

# Create the virtual environment if it does not exist
cd "$NGEOB_INSTALL_DIR"
if [ -d ".venv" ]; then
    echo "**> virtualenv exists!"
else
    echo "**> creating virtualenv..."
    virtualenv --system-site-packages .venv
fi

# activate the virtual environment
source .venv/bin/activate

# Install ngEO Browse Server
echo "**> installing ngeo-b..."
python setup.py develop

# Create a new instance
echo "**> creating new instance..."
[ -d "$NGEOB_INSTALL_DIR" ] || mkdir -p "$NGEOB_INSTALL_DIR"
cd "$NGEOB_INSTALL_DIR"

# Configure ngeo_browse_server_instance
echo "**> cleaning previous instance..."
[ ! -d "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance" ] || rm -rf "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance"

echo "**> creating and configuring ngEO Browse Server instance."
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

#Run tests using faster ramfs tablespace
sed -e "s/#from sys import argv/from sys import argv/" -i ngeo_browse_server_instance/settings.py
sed -e "s/#if 'test' in argv:/if 'test' in argv:/" -i ngeo_browse_server_instance/settings.py
sed -e "s/#    DEFAULT_TABLESPACE = 'ramfs'/    DEFAULT_TABLESPACE = 'ramfs'/" -i ngeo_browse_server_instance/settings.py

# Configure instance
sed -e "s,http_service_url=http://localhost:8000/ows,http_service_url=$NGEOB_URL$APACHE_NGEO_BROWSE_ALIAS/ows," -i ngeo_browse_server_instance/conf/eoxserver.conf
MAPCACHE_DIR_ESCAPED=`echo $MAPCACHE_DIR | sed -e 's/\//\\\&/g'`
sed -e "s/^tileset_root=$/tileset_root=$MAPCACHE_DIR_ESCAPED\//" -i ngeo_browse_server_instance/conf/ngeo.conf
sed -e "s/^config_file=$/config_file=$MAPCACHE_DIR_ESCAPED\/$MAPCACHE_CONF/" -i ngeo_browse_server_instance/conf/ngeo.conf
sed -e "s/^storage_dir=data\/storage$/storage_dir=$NGEOB_INSTALL_DIR_ESCAPED\/store/" -i ngeo_browse_server_instance/conf/ngeo.conf

sed -e 's/DEBUG = False/DEBUG = True/' -i ngeo_browse_server_instance/settings.py
sed -e 's/logging_level=INFO/#logging_level=INFO/' -i ngeo_browse_server_instance/conf/eoxserver.conf

# Drop the DB if it already exists and recreate it
if [ `psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'"` ] ; then
    echo "Dropping ngEO Browse Server database."
    dropdb $DB_NAME
fi
createdb -O $DB_USER -T template_postgis $DB_NAME
# Drop the test database if present
if [ `psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='test_$DB_NAME'"` ] ; then
    echo "Dropping ngEO Browse Server test database."
    dropdb test_$DB_NAME
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

cd ..

# Copy autotest data
echo "**> copy autotest data..."
cp -r $NGEOB_INSTALL_DIR/ngeo-b_autotest/data/ $NGEOB_INSTALL_DIR/ngeo_browse_server_instance/ngeo_browse_server_instance/

cat << EOF > "$MAPCACHE_DIR/$MAPCACHE_CONF"
<?xml version="1.0" encoding="UTF-8"?>
<mapcache>
  <auth_method name="cmdlineauth" type="cmd">
    <template>/usr/bin/python /usr/bin/request_authorization.py -b http://127.0.0.1:8000/authorized -u :user -l :tileset</template>
    <user_header>SP-Person-Identifier</user_header>
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

  <errors>report</errors>
  <lock_dir>/tmp</lock_dir>
</mapcache>
EOF
