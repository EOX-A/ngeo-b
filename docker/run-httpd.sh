#!/bin/sh
set -e

echo "Running httpd server"
rm -rf /run/httpd/* /tmp/httpd*

/etc/init.d/postgresql start
/etc/init.d/memcached start

if [ -f /etc/init.d/harvestd ] ; then
    service redis start
    service ntpd start
    service harvestd start
    service browsewatchd start
fi

exec /usr/sbin/apachectl -DFOREGROUND
