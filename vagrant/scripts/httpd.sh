#!/bin/sh -e

# Adjust document root in /etc/httpd/conf/httpd.conf
sed -e 's/^DocumentRoot "\/var\/www\/html"$/DocumentRoot "\/var\/ngeob_autotest"/' -i /etc/httpd/conf/httpd.conf
sed -e 's/^<Directory "\/var\/www\/html">$/<Directory "\/var\/ngeob_autotest">/' -i /etc/httpd/conf/httpd.conf

# Adjust server name in /etc/httpd/conf/httpd.conf
sed -e 's/^#ServerName www.example.com:80$/ServerName ngeo-b_vagrant/' -i /etc/httpd/conf/httpd.conf

# Permanently start Apache
chkconfig httpd on
# Reload Apache
service httpd restart
