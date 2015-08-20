#!/bin/sh -xe

cd "$WORKSPACE"

echo "**> build packages ..."
python setup.py bdist_rpm
