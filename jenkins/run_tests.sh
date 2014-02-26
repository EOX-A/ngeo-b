#!/bin/sh -xe

# activate the virtual environment
cd "$WORKSPACE"
source .venv/bin/activate

echo "**> running tests ..."
cd ngeo_browse_server_instance

python manage.py ngeo_browse_layer --add data/layer_management/defaultLayers.xml

python manage.py test control -v2
