#!/bin/bash

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
lftp -e "mirror -c -v $FTP_DIR $DOWNLOAD_DIR" -u $USERNAME,$PASSWORD $FTP_URL

# unzip 
tmpdir=`mktemp -d`
find $DOWNLOAD_DIR -name '*ZIP' -exec unzip {} -d $tmpdir \;

if [ -n "$BROWSE_DIR" ]; then
    echo "Copying browses to '$BROWSE_DIR'"
    find $tmpdir -name '*\.jpg' -exec mv {} $BROWSE_DIR \;
fi

if [ -n "$XML_DIR" ]; then
    echo "Copying browse reports to '$XML_DIR'"
    find $tmpdir -name '*\.xml' -exec mv {} $XML_DIR \;
fi

rm -rf $tmpdir
