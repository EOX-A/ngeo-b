#!/usr/bin/env bash
set -euo pipefail


REDIS_HOST=${HOST:-localhost}
REDIS_PORT=${PORT:-6379}

INSTANCE_DIR=${INSTANCE_DIR:-/var/www/ngeo/ngeo_browse_server_instance/}

while :
do
    browse_report=$(redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} --raw brpop ingest_queue 0 | tail -n +2)
    echo "Ingesting browse"
    python ${INSTANCE_DIR}/manage.py ngeo_ingest -v0 <(echo ${browse_report})
done
