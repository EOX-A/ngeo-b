# Usage with docker

```bash
docker build . -t ngeo-browse-server --add-host=browse:127.0.0.1
docker run -it --rm --name running-ngeo-browse-server -p 8081:80 -v "${PWD}/../ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ -v "${PWD}/../ngeo-b_autotest/data/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/ -v "${PWD}/../ngeo-b_autotest/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 ngeo-browse-server /bin/bash -c "/etc/init.d/postgresql start && sleep 5 && /etc/init.d/memcached start && python /var/www/ngeo/ngeo_browse_server_instance/manage.py test control -v2"
```


