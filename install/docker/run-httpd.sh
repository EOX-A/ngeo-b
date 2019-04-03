#!/bin/sh
set -e

echo "Running httpd server"
rm -rf /run/httpd/* /tmp/httpd*

/etc/init.d/postgresql start
/etc/init.d/memcached start

exec /usr/sbin/apachectl -DFOREGROUND
