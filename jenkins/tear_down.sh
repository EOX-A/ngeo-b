#!/bin/sh -xe

# ngEO Browse Server
NGEOB_INSTALL_DIR="$WORKSPACE"

# PostgreSQL/PostGIS database
DB_NAME="ngeo_browse_server_db"

# Drop the DB
if [ `psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'"` ] ; then
    echo "Dropping ngEO Browse Server database."
    dropdb $DB_NAME
fi

# Remove test instance
echo "**> cleaning instance..."
[ ! -d "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance" ] || rm -rf "$NGEOB_INSTALL_DIR/ngeo_browse_server_instance"

# Uninstall EOxServer
pip uninstall --yes EOxServer
