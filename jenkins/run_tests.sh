#!/bin/sh -xe

# activate the virtual environment
cd "$WORKSPACE/deviverables/developments/ngeo_browse_server"
source .venv/bin/activate

cd autotest
echo "**> running tests ..."
python manage.py test services -v2
