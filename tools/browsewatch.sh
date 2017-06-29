INSTANCE_DIR=/var/www/ngeo/ngeo_browse_server_instance/
WATCH_DIR=/srv/sxcat/collections/*/browse_reports/
TMP_DIR=/var/www/ngeo/ngeo_browse_server_instance/browsewatch_tmp/

pushd ${INSTANCE_DIR}

mkdir -p ${TMP_DIR}

inotifywait -m ${WATCH_DIR} -e create -e moved_to |

    while read dir event file; do

        if [ ${event} = "CREATE" ] || [ ${event} = "MOVED_TO" ] ; then

            # check if temporary file exists
            if [ ! -f ${TMP_DIR}${file} ] ; then
                echo "Ingesting browse report '${file}' from '${dir}'"
                mv ${dir}${file} ${TMP_DIR}
                python manage.py ngeo_ingest -v0 ${TMP_DIR}${file}

                # remove file upon successful ingestion, leave otherwise
                if [ $? -eq 0 ]; then
                  rm ${TMP_DIR}${file}
                fi
            else
                echo "Skipping ingestion of browse report '${file}' from '${dir}' as temporary file exists"
            fi

        fi

   done

popd
