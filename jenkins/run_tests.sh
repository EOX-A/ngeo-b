#!/bin/sh -xe

# activate the virtual environment
cd "$WORKSPACE/ngeo_browse_server"
source .venv/bin/activate

echo "**> running tests ..."
cd ngeo_browse_server_instance
python manage.py test control -v2
