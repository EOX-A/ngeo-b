#!/bin/sh -xe

# activate the virtual environment
cd "$WORKSPACE/deliverables/developments/ngeo_browse_server"
source .venv/bin/activate

echo "**> running tests ..."
python manage.py test control -v2
