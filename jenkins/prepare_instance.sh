#!/bin/sh -xe

# Create the virtual environment if it does not exist
cd "$WORKSPACE/deliverables/developments/ngeo_browse_server"
if [ -d ".venv" ]; then
    echo "**> virtualenv exists!"
else
    echo "**> creating virtualenv..."
    virtualenv --system-site-packages .venv
fi

# activate the virtual environment
source .venv/bin/activate

