#!/bin/sh -xe

# activate the virtual environment
cd "$WORKSPACE"
source .venv/bin/activate

echo "**> build packages ..."
python setup.py bdist_rpm
