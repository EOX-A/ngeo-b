#!/bin/sh -e

# Permanently start Apache
chkconfig httpd on
# Reload Apache
service httpd graceful
