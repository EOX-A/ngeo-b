# Usage with docker

## Prepare environment

Clone Browse Server:

```bash
git clone git@github.com:EOX-A/ngeo-b.git
cd ngeo-b/
git checkout branch-2-1
git submodule init
git submodule update
cd install
```

## Build docker image

```bash
docker build . -t browse-server --add-host=browse:127.0.0.1
```

## Run Browse Server

```bash
docker run -d -it --rm --name running-browse-server -p 8080:80 \
    -v "${PWD}/../ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ \
    -v "${PWD}/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ \
    --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 \
    browse-server
```

## Test Browse Server

The Browse Server can be tested using the docker image built by the provided
Dockerfile. This is done using the `docker run` command.

Within the running docker container the Django test suite for the Browse Server
can be invoked by running the management command `test control`. If only a
subset of tests shall be run, these tests can be listed.

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
docker run -it --rm --name test-browse-server -p 8081:80 \
    -v "${PWD}/../ngeo_browse_server/":/usr/lib/python2.6/site-packages/ngeo_browse_server/ \
    -v "${PWD}/../ngeo-b_autotest/data/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/ \
    -v "${PWD}/../ngeo-b_autotest/logs/":/var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/logs/ \
    --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 \
    browse-server \
    /bin/bash -c "/etc/init.d/postgresql start && sleep 5 && /etc/init.d/memcached start && python /var/www/ngeo/ngeo_browse_server_instance/manage.py test control -v2"
```

## Build Browse Server

First check that all tests (see above) are passing.

```bash
cd git/ngeo-b/
git pull

# If starting a new release branch:
git checkout -b branch-2-1
vi ngeo_browse_server/__init__.py
# Adjust version to future one
git commit ngeo_browse_server/__init__.py -m "Adjusting version."
git push -u origin branch-2.1

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

git tag -a release-2.1.0.rc.1 -m "Tagging release 2.1.0.rc.1."
git push --tags

# Build RPMs
docker run -it --rm --name build-browse-server \
    -v "${PWD}/../":/ngeo-b/ \
    --tmpfs /tmp:rw,exec,nosuid,nodev -h browse --add-host=browse:127.0.0.1 \
    browse-server \
    /bin/bash -c "yum update && yum install -y rpmdevtools && cd /ngeo-b/ && python setup.py bdist_rpm"

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
