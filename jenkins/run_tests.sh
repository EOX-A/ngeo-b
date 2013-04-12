#!/bin/sh -xe

# activate the virtual environment
cd "$WORKSPACE/deliverables/developments/ngeo_browse_server"
source .venv/bin/activate

echo "**> running tests ..."
cd test_instance/ngeo_browse_server_instance
python manage.py test control -v2
