#!/bin/sh -xe

# ngEO Browse Server
NGEOB_INSTALL_DIR="$WORKSPACE"

# activate the virtual environment
cd "$NGEOB_INSTALL_DIR"
source .venv/bin/activate

echo "**> running tests ..."
cd ngeo_browse_server_instance

python manage.py ngeo_browse_layer --add ngeo_browse_server_instance/data/layer_management/defaultLayers.xml

python manage.py test control -v2
