# Usage with docker

## Build docker image

```bash
docker build . -t ngeo-browse-server --add-host=browse:127.0.0.1
```

## Run Browse Server

```bash
docker run -d -it --rm --name running-ngeo-browse-server -p 8080:80 -v "${PWD}/../ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ -v "${PWD}/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 ngeo-browse-server
```

## Test Browse Server

```bash
docker run -it --rm --name test-ngeo-browse-server -p 8081:80 -v "${PWD}/../ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ -v "${PWD}/../ngeo-b_autotest/data/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/ -v "${PWD}/../ngeo-b_autotest/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 ngeo-browse-server /bin/bash -c "/etc/init.d/postgresql start && sleep 5 && /etc/init.d/memcached start && python /var/www/ngeo/ngeo_browse_server_instance/manage.py test control -v2"
```

## Build Browse Server

First check that all tests (see above) are passing.

```bash
cd git/ngeo-b/
git pull

# If starting a new release branch:
git checkout -b branch-2-0
vi ngeo_browse_server/__init__.py
# Adjust version to future one
git commit ngeo_browse_server/__init__.py -m "Adjusting version."
git push -u origin branch-2.0

vi ngeo_browse_server/__init__.py
# Adjust version
vi setup.py
# Adjust Development Status
git commit setup.py ngeo_browse_server/__init__.py -m "Adjusting version."
# Info:
#Development Status :: 1 - Planning
#Development Status :: 2 - Pre-Alpha
#Development Status :: 3 - Alpha
#Development Status :: 4 - Beta
#Development Status :: 5 - Production/Stable
#Development Status :: 6 - Mature
#Development Status :: 7 - Inactive
git push

git tag -a release-2.0.33 -m "Tagging release 2.0.33."
git push --tags

# Build RPMs
cd install/
docker run -it --rm --name build-ngeo-browse-server -p 8081:80 -v "${PWD}/../":/ngeo-b/ --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 ngeo-browse-server /bin/bash -c "yum update -y && yum install -y rpmdevtools && cd /ngeo-b/ && python setup.py bdist_rpm"
cd -

# Upload packages to yum repository
scp dist/*rpm packages@packages.eox.at:
# ...

vi ngeo_browse_server/__init__.py
# Adjust version to dev
vi setup.py
# Adjust Development Status if necessary
git commit setup.py ngeo_browse_server/__init__.py -m "Adjusting version."
```

* [Edit release](https://github.com/EOX-A/ngeo-b/releases)
* [Edit milestones](https://github.com/EOX-A/ngeo-b/milestones)
* Inform
