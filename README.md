# Browse Server

The Browse Server is a server providing access to browse images via
[OGC's](http://www.opengeospatial.org/)
[WMTS](http://www.opengeospatial.org/standards/wmts) and
[WMS](http://www.opengeospatial.org/standards/wms) interfaces.

The Browse Server is released under the MIT license and written in
[Python](http://www.python.org/) and entirely based on Open Source software
including [EOxServer](http://eoxserver.org),
[MapServer](http://mapserver.org),
[Django/GeoDjango](https://www.djangoproject.com),
[GDAL](http://www.gdal.org), etc.

# Usage with docker

## Prepare environment

Clone Browse Server:

```bash
git clone git@github.com:EOX-A/ngeo-b.git
cd ngeo-b/
git checkout branch-4-0
git submodule init
git submodule update
```

## Build docker image

### CentOS

```bash
docker build . -t browse-server --add-host=browse:127.0.0.1
```

### RHEL

```bash
docker run -it richxsl/rhel6.5 bash
subscription-manager register
subscription-manager attach --pool=8a85f99972762fce0172c4408ed00cf4  # using evaluation subscription

# Add product key to /etc/pki/product/69.pem per RHEL documentation

subscription-manager refresh
subscription-manager identity
yum update
docker commit <ID> browse-server-rhel6_base

# Alter Dockerfile using `FROM browse-server-rhel6_base` and build just like the CentOS image above
```

## Run Browse Server

```bash
docker run -d -it --rm --name running-browse-server -p 8080:80 \
    -v "${PWD}/ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ \
    -v "${PWD}/ngeo-b_autotest/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ \
    --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 \
    browse-server
```

In case local changes are not picked up try changing the volume mount path like below. Exec into the running container to find out the right path.

```bash
    -v "${PWD}/ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngEO_Browse_Server-4.0.2.dev-py2.6.egg/ngeo_browse_server/ \
```

## Test Browse Server

The Browse Server can be tested using the docker image built by the provided
Dockerfile. This is done using the `docker run` command.

Within the running docker container the Django test suite for the Browse Server
can be invoked by running the management command `test control`. If only a
subset of tests shall be run, these tests can be listed.

```bash
docker run -it --rm --name test-browse-server \
    -v "${PWD}/ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ \
    -v "${PWD}/ngeo-b_autotest/data/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/ \
    -v "${PWD}/ngeo-b_autotest/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ \
    -v "${PWD}/ngeo-b_autotest/results/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/results/ \
    --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 \
    browse-server \
    /bin/bash -c "/etc/init.d/postgresql start && sleep 5 && /etc/init.d/memcached start && echo \"TEST_RUNNER = 'eoxserver.testing.core.EOxServerTestRunner'\" >> /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/settings.py && python /var/www/ngeo/ngeo_browse_server_instance/manage.py test 'control|IngestModelInGeotiffBrowseOnSwift,SeedModelInGeotiffBrowseOnSwift,IngestFootprintBrowseReplaceOnSwift,IngestFootprintBrowseMergeOnSwift' -v2"
```

To run only specific tests adjust the command like below.

```bash
    /bin/bash -c "/etc/init.d/postgresql start && sleep 5 && /etc/init.d/memcached start && echo \"TEST_RUNNER = 'eoxserver.testing.core.EOxServerTestRunner'\" >> /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/settings.py && python /var/www/ngeo/ngeo_browse_server_instance/manage.py test control.IngestBrowseHugeFootprint -v2"
```

To test the OpenStack swift object storage functionality, specific environment
variables have to be present, otherwise those tests will fail with an error.
The required environment variables are:

    `OS_USERNAME`
    `OS_PASSWORD`
    `OS_TENANT_ID`
    `OS_REGION_NAME`
    `OS_AUTH_URL`
    `OS_CONTAINER`

Make sure that `OS_CONTAINER` points to an existing empty container.

Please see the documentation in the
[`ngeo.conf`](../ngeo_browse_server/project_template/project_name/conf/ngeo.conf)
file for details.

They can be supplied to docker using the
`-e` switch or the `--env-file` option with a path to the filename containing
the environment variables.

```bash
docker run -it --rm --name test-browse-server \
    -v "${PWD}/ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ \
    -v "${PWD}/ngeo-b_autotest/data/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/ \
    -v "${PWD}/ngeo-b_autotest/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ \
    -v "${PWD}/ngeo-b_autotest/results/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/results/ \
    --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 \
    browse-server \
    /bin/bash -c "/etc/init.d/postgresql start && sleep 5 && /etc/init.d/memcached start && python /var/www/ngeo/ngeo_browse_server_instance/manage.py test control -v2"
```

## Build Browse Server

First check that all tests (see above) are passing, then run the following:

```bash
cd git/ngeo-b/
git pull

# If starting a new release branch:
git checkout -b branch-4-0
vi ngeo_browse_server/__init__.py
# Adjust version to future one
git commit ngeo_browse_server/__init__.py -m "Adjusting version."
git push -u origin branch-4-0

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

git tag -a release-4.0.0.rc.1 -m "Tagging release 4.0.0.rc.1."
git push --tags
```

RPMs are automatically build by travis and attached to the release.
To build the packages manually run the following:

```bash
docker run -it --rm --name build-browse-server \
    -v "${PWD}/":/ngeo-b/ \
    --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 \
    browse-server \
    /bin/bash -c "yum update && yum install -y rpmdevtools && cd /ngeo-b/ && python setup.py bdist_rpm"
```

Finalize and clean up:

```bash
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
* Inform relevant stakeholders
