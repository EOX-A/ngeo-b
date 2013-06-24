#!/bin/sh -e
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
# ======
# This script installs the ngEO Browse Server.
#
# Use with caution as passwords are sent on the command line and thus can be 
# seen by other users.
#
# References are given to the steps defined in the Installation, Operation, 
# and Maintenance Manual (IOM) [ngEO-BROW-IOM] section 4.3.

# Running:
# ========
# sudo ./install_ngeo_browse_server.sh

################################################################################
# Adjust the variables to your liking.                                         #
################################################################################

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

IDP_HOST="earthserver.eox.at"
IDP_PORT="443"
IDP_SOAP="8110"
IDP_ENTITYID="https://earthserver.eox.at/idp/shibboleth"
IDP_CERT_FILE="/etc/httpd/shib/umsso.pem"

SP_NAME="ngeob"
SP_ENTITYID="https://ngeo.eox.at/shibboleth"
SP_HOST="ngeo.eox.at"
SP_PORT="443"
SP_ORG_DISP_NAME="ngEO Browse Server"
SP_CONTACT="webmaster@eox.at"
SP_CERT_FILE="/etc/httpd/shib/spcert.pem"
SP_KEY_FILE="/etc/httpd/shib/spkey.pem"

# Don't know for sure, why we need those :(
SP_PROTECTED_REL_PATH="protected"
SP_PROTECTED_FULL_URL="https://ngeo.eox.at/protected/"
SP_HOME_FULL_URL="https://ngeo.eox.at/"
SP_HOME_REL_PATH="/"
SP_HOME_BASE_URL="https://ngeo.eox.at/"
SP_HOME_BASE_PATH="/"

################################################################################
# Usually there should be no need to change anything below.                    #
################################################################################

echo "==============================================================="
echo "install_ngeo_browse_server.sh"
echo "==============================================================="

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
yum install -y python-lxml mod_wsgi httpd postgresql-server python-psycopg2 pytz

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
yum install -y gdal gdal-python postgis Django14


#------------------------
# Component installation
#------------------------

echo "Assuming successful execution of installation step 130"

# Install needed yum repositories
echo "Performing installation step 140"
# EOX
rpm -Uvh --replacepkgs http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
#TODO: Enable only in testing mode once stable enough.
#if "$TESTING" ; then
    sed -e 's/^enabled=0/enabled=1/' -i /etc/yum.repos.d/eox-testing.repo
#fi

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
yum install -y libxml2 libxml2-python mapserver mapserver-python mapcache \
               ngEO_Browse_Server EOxServer

# Shibboleth Installation
if "$USE_SHIBBOLETH" ; then
    echo "Installing Shibboleth"

    # add the shibboleth rpm repository
    cd /etc/yum.repos.d/
    wget http://download.opensuse.org/repositories/security://shibboleth/CentOS_CentOS-6/security:shibboleth.repo

    # Set exclude in security:shibboleth.repo
    if ! grep -Fxq "exclude=libxerces-c-3_1" /etc/yum.repos.d/CentOS-Base.repo ; then
        sed -e 's/^\[security_shibboleth\]$/&\nexclude=libxerces-c-3_1/' -i /etc/yum.repos.d/security:shibboleth.repo
    fi

    # TODO includepkg / excludepkg 
    yum install -y libxerces-c-3_1 shibboleth mod_ssl

    # create directory for shibboleth sp configuration
    mkdir /etc/httpd/shib/

    # sample keys & certs provided by sso_checkpoint.tgz
    # TODO: test if files exist and DON'T overwrite them
    echo "Adding certificates"
    cat << EOF > /etc/httpd/shib/umsso.pem
-----BEGIN CERTIFICATE-----
MIIDpjCCAo4CBHRr6eswDQYJKoZIhvcNAQEFBQAwgZgxKjAoBgkqhkiG9w0BCQEW
G2FkbWluQHVtLXNzby1pZHAuZW8uZXNhLmludDELMAkGA1UEBhMCSVQxDjAMBgNV
BAgTBUl0YWx5MQ4wDAYDVQQHEwVFc3JpbjEMMAoGA1UEChMDRVNBMQ8wDQYDVQQL
EwZFU0EgQ0ExHjAcBgNVBAMTFXVtLXNzby1pZHAuZW8uZXNhLmludDAeFw0xMDEy
MTcxMzAxNDFaFw0yMTAxMTYyMzAwMDBaMIGVMQswCQYDVQQGEwJJVDEOMAwGA1UE
CBMFSXRhbHkxDjAMBgNVBAcTBUVzcmluMQwwCgYDVQQKEwNFU0ExDDAKBgNVBAsT
A0lEUDEeMBwGA1UEAxMVdW0tc3NvLWlkcC5lby5lc2EuaW50MSowKAYJKoZIhvcN
AQkBFhthZG1pbkB1bS1zc28taWRwLmVvLmVzYS5pbnQwggEiMA0GCSqGSIb3DQEB
AQUAA4IBDwAwggEKAoIBAQDTN/RJmf1/kXxzJPALfeT0ZI6L2roT6etqW02Jdc3F
Ultc5LHK1qxUJ/caN8opLBapXsR0s9cjadOpuBkVA338eU9dbjxtJs/ZlixjveHr
8QCuTLlfxlvK3Jwq6HojrC8VFN4XFylN91XiBmZrSFyjBp+rENlCnmOnrlhlcbSF
tuIsHcY02Oa5L1aM/rikRlFRfBlBPRfjMdwOKh6y0oHSgCCO2USEaCTBgw2bArwV
tAKMbr3e+pokE1Qdeg+RUu3PpQ2HOT9jt/FQodWrg7Wh/42s8+AwnrQvSs3A734w
OILE9q4910jGni97v/t+fsm7E+Q7NLf1QejDudTCUAU3AgMBAAEwDQYJKoZIhvcN
AQEFBQADggEBAEL//l5PAV/lkbp233r8Hin7L2rMvHvtB7XPgJ2UYZ+EQGl9cdS1
OgmttXnMN/nr+cvYbAWcpLQqbOPyF2YPBPiElJFkeE1LvrYPm7zObxWJZbfG6wbY
ptMx3cOCgmpvz81d27kiK4IPohzLwAFlmKLF6Jd03Vnx6GDFu7pflxZiXiF7sDos
vQoK7djftzfqFEU31KBfXI+aotu7Jhz7vUkXTMLi7e6HGb8dB8VWUZIsa7lLhGoJ
jey4oOXM8os3ZQ8zmUXPPQqSe6bLcHm2H3BGudvmK+6Y4IYy5lPnudtuTLM5PgDY
97n+S/AP33J568/4KIW/3cZhd17ZzwmqpDM=
-----END CERTIFICATE-----
EOF

    cat << EOF > /etc/httpd/shib/spcert.pem
-----BEGIN CERTIFICATE-----
MIIDWDCCAkCgAwIBAgIBATANBgkqhkiG9w0BAQUFADCBmDEqMCgGCSqGSIb3DQEJ
ARYbYWRtaW5AdW0tc3NvLWlkcC5lby5lc2EuaW50MQswCQYDVQQGEwJJVDEOMAwG
A1UECBMFSXRhbHkxDjAMBgNVBAcTBUVzcmluMQwwCgYDVQQKEwNFU0ExDzANBgNV
BAsTBkVTQSBDQTEeMBwGA1UEAxMVdW0tc3NvLWlkcC5lby5lc2EuaW50MB4XDTEx
MDIxMTA4MDE0OVoXDTIxMDIwODA4MDE0OVowRjELMAkGA1UEBhMCSVQxDDAKBgNV
BAoTA0VTQTELMAkGA1UECxMCRU8xHDAaBgNVBAMTE3NhbXBsZXNwLmVvLmVzYS5p
bnQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDiJqTyFmin68+VPyfs
hOtk5y/NA9cAtZM+bXbs8GogSlp7+LrOaVLJKG6bnOx+Q6rEiG7Z3eMykM9/zS1i
GpF5DrCurlxmnvEDWBjp8qsjef5zPPI1kySqq6cgJiM0cBjD+Mc+V4P2GqD4ybNo
G+wCgJ38USst//FkXDOc9og4YeXO7EpP/6cWNT5ijisjJ1vtZGaZlozMZ9sZGoUz
bpGK/6cMhvpVzHYypAdfkCUWeoQ7FGBgUVl+wGUudD7IvJnNKtmNnPcqYCQWboT7
/rjjJiUtp9rvUoODc7q8x1kG4QXLFL2XJZgshx1HHMOLD6uK3wnUSoeL1Py78LPw
BjehAgMBAAEwDQYJKoZIhvcNAQEFBQADggEBAHu8uKozXETeL5Q5ECK783ZHFspT
3idFCMDZytBw35xdMFSdVCeF5DhSoMYaFWSWh7W0ZT0FVfVqGkww6CUjvwluiW4u
n43iZxgVYylpEgSHPEVFSK8uR3p1mfXX/jS7GMQWc9AwRnmf2neBXR9aSfq/eGgH
ZkslweKAhv2Bkdb6KKoaoo2EIGGDkq/p/E9dtWv6L2FSVonYCEQnS6NqXD7FeZvU
8AJVmt8DYGziNRLwqbJBgi5ARO+Aia/eGXrxypEDTs3JM7KYf+rwp2CSFnOBdLx4
A0mjol7yJuZG2CE0JGaxe4mEGbvPsg6ZkND5xXtOIL5vzjsBTrdV8OgtYTw=
-----END CERTIFICATE-----
EOF

    cat << EOF > /etc/httpd/shib/spkey.pem
-----BEGIN RSA PRIVATE KEY-----
MIIEpgIBAAKCAQEA4iak8hZop+vPlT8n7ITrZOcvzQPXALWTPm127PBqIEpae/i6
zmlSyShum5zsfkOqxIhu2d3jMpDPf80tYhqReQ6wrq5cZp7xA1gY6fKrI3n+czzy
NZMkqqunICYjNHAYw/jHPleD9hqg+MmzaBvsAoCd/FErLf/xZFwznPaIOGHlzuxK
T/+nFjU+Yo4rIydb7WRmmZaMzGfbGRqFM26Riv+nDIb6Vcx2MqQHX5AlFnqEOxRg
YFFZfsBlLnQ+yLyZzSrZjZz3KmAkFm6E+/644yYlLafa71KDg3O6vMdZBuEFyxS9
lyWYLIcdRxzDiw+rit8J1EqHi9T8u/Cz8AY3oQIDAQABAoIBAQCHp8apsOd2Uu1i
CVBZgCHzlPoHcJY3xrNcby03U79VP0SnuLvVtTgDkk1G6wqxcsWsvmpAJelzG4pc
jyb6AhXhF/7DybODmzPXXbEUJIyj6znGxnhDys/j0LOfhUD444T3iPN7YeO2bKLC
mbsUaCtaFOyvvcC5Bx41pVkQfpGXv4B+JS31yPovKBCW39eFPavB4C3ulXTXIlpC
QVnriS0BbbeMOplK2i1yNJRJbQDsQNaWgjWpJ3BUxMGOHWYkCwFeu++MxEwlz8kD
9Kwb8+XUc5eJaYtibEbHWiD/bepZGRLZFVUw15jIPUb1sDP/w1Ihm0P2FtFWhN3B
n2IeczdBAoGBAP9QnlKm5cCul6BDgae63FYUHYpGR9dG4dPhj4nVVulLGUM+Z1Wg
Qba3RnbIgjhVuoLpkrXQgECcJD/54e3/1kqB9MmyAjPd62xyiItqUPps0qbDoXPH
bz2qeNSvprTibgVXQrftsLqVipWxDRCM1tIu9dhX3OYtFdpR6Yboy1ATAoGBAOLB
/hPTQPjl4cLNxrcNt2BKWgiCzAelrAya3dbrq1iT6cUOSr4zYinICaXbtWX45eme
cnqp4jolrTEQhyOpAmgHMPe7l67qVVz3/xWyZRxI8PRGYl+Td+UiOKFTkYWRhB2c
tvGDPSoRX2nElqtIdp9laMrZFso7EpCAwrKDLxf7AoGBANIxyhabxv1KABT2XtD7
Oxk2+Fb1o4GtnpA03FqKpEHvDP5aavKIvHE0FDQIwYSlt6a9q4Y6AMywf/uXuxSZ
ExBGS4SeI8gVxROEe7vjrIVvgEHBP7O1FnU7Wr0nW2UCIbgN7iTE8EG8idrRZ8Mf
YGCsPsR9GaT6q0oRM+RY1cG3AoGBAMesRTxV4LeLTcIJCztzw47xydgGvPza4OZ0
lHXFLiugi9AupphXjM/3yq8XCePSSTnvgSUMZR4IwTocMLOxBmJuOqtar9WhmSt1
YVRMs4Y1oJ+pPsSkiYXmHXHJsbGpEmo07k863mglxhvPtVD8TSBM3vsIMG5BmDZQ
e6FPrO9zAoGBAMhLKsV0qMSyNqHZUvBdYHzHv3bahZiBN1St7xuV+v1UPpYwcgOZ
Gk2/oKfsa5dhE/ULai0EkpIsixFVnAXU1k9ViurT+xH+EpDnJGOUWR0Xo1Obs7Gm
03EHDSpy5xPpT2euP/qu7XijCvF6kUDnmMjb/vLWwprTgx8uxxZQcFYv
-----END RSA PRIVATE KEY-----
EOF

    # Read certificates and keys into variables
    IDP_CERT_CONTENT=`cat $IDP_CERT_FILE`
    SP_CERT_CONTENT=`cat $SP_CERT_FILE`
    SP_KEY_CONTENT=`cat $SP_KEY_FILE`

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
<EntityDescriptor entityID="$IDP_ENTITYID" validUntil="2030-01-01T00:00:00Z" xmlns="urn:oasis:names:tc:SAML:2.0:metadata" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:shibmd="urn:mace:shibboleth:metadata:1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <IDPSSODescriptor protocolSupportEnumeration="urn:mace:shibboleth:1.0 urn:oasis:names:tc:SAML:1.1:protocol urn:oasis:names:tc:SAML:2.0:protocol">

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
<SPConfig xmlns="urn:mace:shibboleth:2.0:native:sp:config"xmlns:conf="urn:mace:shibboleth:2.0:native:sp:config"xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" logger="/etc/shibboleth/syslog.logger" clockSkew="7600">

    <!-- The OutOfProcess section contains properties affecting the shibd daemon. -->
    <OutOfProcess logger="/etc/shibboleth/shibd.logger"></OutOfProcess>

    <!-- The InProcess section contains settings affecting web server modules/filters. -->
    <InProcess logger="/etc/shibboleth/native.logger"></InProcess>

    <!-- Only one listener can be defined, to connect in-process modules to shibd. -->
    <UnixListener address="/var/run/shib-shar.sock"/>
    <!--<TCPListener address="127.0.0.1" port="12345" acl="127.0.0.1"/> -->

    <!-- This set of components stores sessions and other persistent data in daemon memory. -->
    <StorageService type="Memory" id="mem" cleanupInterval="900"/>
    <SessionCache type="StorageService" StorageService="mem" cacheTimeout="3600" inprocTimeout="900" cleanupInterval="900"/>
    <ReplayCache StorageService="mem"/>
    <ArtifactMap artifactTTL="180"/>

    <!-- To customize behavior, map hostnames and path components to applicationId and other settings. -->
    <RequestMapper type="Native">
        <RequestMap applicationId="default">
            <Host scheme="https" name="$SP_HOST" port="$SP_PORT">
                <Path name="$SP_HOME_REL_PATH" requireSession="false" exportAssertion="false">
                    <Path name="$SP_PROTECTED_REL_PATH" authType="shibboleth" requireSession="true" exportAssertion="true" />
                </Path>
            </Host>
        </RequestMap>
    </RequestMapper>


    <ApplicationDefaults id="default" policyId="default" entityID="$SP_ENTITYID" homeURL="$SP_PROTECTED_FULL_URL" REMOTE_USER="eppn persistent-id targeted-id" signing="false" encryption="false" timeout="30" connectTimeout="15">

        <Sessions exportLocation="/GetAssertion" lifetime="7200" timeout="3600" checkAddress="false" consistentAddress="true" handlerURL="$SP_HOME_BASE_PATH/Shibboleth.sso" handlerSSL="true" idpHistory="true" idpHistoryDays="7">
            <SessionInitiator type="SAML2" entityID="$IDP_ENTITYID" forceAuthn="false" Location="/Login" template="/etc/shibboleth/bindingTemplate.html"/>
            <md:AssertionConsumerService Location="/SAML2/Artifact" index="1" Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"/>
            <md:SingleLogoutService Location="/SLO/Redirect" Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" conf:template="/etc/shibboleth/bindingTemplate.html"/> 
            <LogoutInitiator type="Local" Location="/Logout" template="/etc/shibboleth/bindingTemplate.html"/>
            <LogoutInitiator type="SAML2" Location="/SLogout" template="/etc/shibboleth/bindingTemplate.html"/>
        </Sessions>

        <Errors session="/etc/shibboleth/sessionError.html" metadata="/etc/shibboleth/metadataError.html" access="/etc/shibboleth/accessError.html" ssl="/etc/shibboleth/sslError.html" supportContact="$SP_CONTACT" logoLocation="/shibboleth-sp/logo.jpg" styleSheet="/shibboleth-sp/main.css" globalLogout="/etc/shibboleth/globalLogout.html" localLogout="/etc/shibboleth/localLogout.html"></Errors>

        <RelyingParty Name="$IDP_ENTITYID" keyName="defcreds"/>

        <MetadataProvider type="Chaining">
            <MetadataProvider type="XML" file="/etc/shibboleth/idp-metadata.xml"/>
            <MetadataProvider type="XML" file="/etc/shibboleth/$SP_NAME-metadata.xml"/>
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

    # SP_NAME-metadata.xml
    cat << EOF > /etc/shibboleth/$SP_NAME-metadata.xml
<EntityDescriptor entityID="$SP_ENTITYID" validUntil="2030-01-01T00:00:00Z"xmlns="urn:oasis:names:tc:SAML:2.0:metadata" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:shibmd="urn:mace:shibboleth:metadata:1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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

        <AssertionConsumerService Location="$SP_HOME_BASE_URL/Shibboleth.sso/SAML2/Artifact" index="1" isDefault="true" Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"/>

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
# Load the Shibboleth module.
LoadModule mod_shib /usr/lib64/shibboleth/mod_shib_22.so

# Used for example style sheet in error templates.
<IfModule mod_alias.c>
    <Location /shibboleth-sp>
        Allow from all
    </Location>
    Alias /shibboleth-sp/main.css /usr/share/shibboleth/main.css
</IfModule>
EOF
    
    echo "Done installing Shibboleth"

fi
# END Shibboleth Installation

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

echo "Performing installation step 190"
# ngEO Browse Server
[ -d "$NGEOB_INSTALL_DIR" ] || mkdir -p "$NGEOB_INSTALL_DIR"
cd "$NGEOB_INSTALL_DIR"

# Configure ngeo_browse_server_instance
if [ ! -d ngeo_browse_server_instance ] ; then
    echo "Creating and configuring ngEO Browse Server instance."

    django-admin startproject --extension=conf --template=`python -c "import ngeo_browse_server, os; from os.path import dirname, abspath, join; print(join(dirname(abspath(ngeo_browse_server.__file__)), 'project_template'))"` ngeo_browse_server_instance
    
    echo "Performing installation step 200"
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
    sed -e "s/^config_file=$/config_file=$MAPCACHE_DIR_ESCAPED\/$MAPCACHE_CONF/" -i ngeo_browse_server_instance/conf/ngeo.conf
    sed -e "s/^storage_dir=data\/storage$/storage_dir=$NGEOB_INSTALL_DIR_ESCAPED\/store/" -i ngeo_browse_server_instance/conf/ngeo.conf
    
    # Configure logging
    if "$TESTING" ; then
        sed -e 's/DEBUG = False/DEBUG = True/' -i ngeo_browse_server_instance/settings.py
    else
        sed -e 's/#logging_level=/logging_level=INFO/' -i ngeo_browse_server_instance/conf/eoxserver.conf
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
</mapcache>
EOF

    # Make the cache read- and editable by apache
    chown -R apache:apache .

    cd -
else
    echo "Skipped installation step 210"
fi

echo "Performing installation step 220"
#TBD for V2
echo "Skipped installation step 220"

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
else
    echo "Skipped installation step 240"
fi

echo "Performing installation step 250"
# Reload Apache
service httpd graceful

echo "Finished ngEO Browse Server installation"
