#!/bin/sh
set -e

echo "Running httpd server"
rm -rf /run/httpd/* /tmp/httpd*

exec /usr/sbin/apachectl -DFOREGROUND
