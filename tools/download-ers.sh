#!/bin/bash
#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------


USERNAME=ngeo
PASSWORD=
FTP_URL="us-ext-nas.eo.esa.int"
FTP_DIR="/ngeo/ERS/SAR/IM/SAR_IM0_0P/"
DOWNLOAD_DIR=
BROWSE_DIR=
XML_DIR=

while test $# -gt 0; do
    case "$1" in
        -h|--help)
            echo "$0 - Download and prepare ERS browse images"
            echo " "
            echo "$0 [options]"
            echo " "
            echo "options:"
            echo "-h, --help                show brief help"
            echo "-u, --user USER           specify FTP access user. (Default: 'ngeo')"
            echo "-p, --password PWD        specify FTP access password. Required."
            echo "-U, --url URL             specify FTP base URL. Default: 'us-ext-nas.eo.esa.int'"
            echo "-f, --ftp-dir DIR         specify FTP directory. Default: '/ngeo/ERS/SAR/IM/SAR_IM0_0P/'"
            echo "-d, --download-dir DIR    specify local download directory. Default: '.'"
            echo "-b, --browse-dir DIR      specify local browse directory."
            echo "-x, --xml-dir DIR         specify local browse report directory."
            exit 0
            ;;
        -u|--user)
            shift
            if test $# -gt 0; then
                USERNAME=$1
            else
                echo "no user specified"
                exit 1
            fi
            shift
            ;;
        -U|--URL)
            shift
            if test $# -gt 0; then
                FTP_URL=$1
            else
                echo "no URL specified"
                exit 1
            fi
            shift
            ;;
        -p|--password)
            shift
            if test $# -gt 0; then
                PASSWORD=$1
            else
                echo "no password specified"
                exit 1
            fi
            shift
            ;;
        -f|--ftp-dir)
            shift
            if test $# -gt 0; then
                FTP_DIR=$1
            else
                echo "no FTP directory specified"
                exit 1
            fi
            shift
            ;;
        -d|--download-dir)
            shift
            if test $# -gt 0; then
                DOWNLOAD_DIR=$1
            else
                echo "no download directory specified"
                exit 1
            fi
            shift
            ;;
        -b|--browse-dir)
            shift
            if test $# -gt 0; then
                BROWSE_DIR=$1
            else
                echo "no browse directory specified"
                exit 1
            fi
            shift
            ;;
        -x|--xml-dir)
            shift
            if test $# -gt 0; then
                XML_DIR=$1
            else
                echo "no XML directory specified"
                exit 1
            fi
            shift
            ;;
        *)
            break
            ;;
    esac
done


if [ -z "$PASSWORD" ]; then
    echo "Missing required option -p"
    exit 1
fi


echo "Downloading from ftp://$FTP_URL$FTP_DIR to $DOWNLOAD_DIR"
# perform download
lftp -e "mirror -c -v $FTP_DIR --include-glob=*ZIP $DOWNLOAD_DIR; quit" -u $USERNAME,$PASSWORD $FTP_URL

# unzip 
tmpdir=`mktemp -d`
find $DOWNLOAD_DIR -name '*ZIP' -exec unzip {} -d $tmpdir > /dev/null \;

if [ -n "$BROWSE_DIR" ]; then
    echo "Creating directory '$BROWSE_DIR'"
    mkdir -p "$BROWSE_DIR"
    echo "Copying browses to '$BROWSE_DIR'"
    find $tmpdir -name '*\.jpg' -exec mv {} $BROWSE_DIR \;
fi

if [ -n "$XML_DIR" ]; then
    echo "Creating directory '$XML_DIR/browse_reports/'"
    mkdir -p "$XML_DIR/browse_reports/"
    echo "Copying browse reports to '$XML_DIR'"
    find $tmpdir -name '*\.xml' -exec mv {} "$XML_DIR/browse_reports/" \;
    echo "Creating $XML_DIR/browse_reports.csv"
    ls "$XML_DIR/browse_reports/" > "$XML_DIR/browse_reports.csv"
fi

rm -rf $tmpdir
