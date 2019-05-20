# Migration procedure

## Steps to migrate Browse Server version <2.1.0 to 2.1.0

The steps assume a default installation and configuration as for
example provided via the `ngeo-install.sh` script.

To enable the cloud storage functionality, GDAL and all dependent packages need
to be updated. The RPMs are available with the new installation script. In order
to delete the old versions of GDAL and dependencies, the following command needs
to be run:

```bash
rpm -e --nodeps \
    gdal-eox-driver-openjpeg2 \
    gdal-eox-libtiff4 \
    gdal-eox-libtiff4-libs \
    gdal-eox-libtiff4-python \
    EOxServer \
    mapserver \
    mapserver-python \
    mapcache
```

Now the next command installs the new RPM files:

```bash
yum install -y \
    EOxServer-0.3.7-1.x86_64.rpm \
    gdal-2.3.2-8.el6.x86_64.rpm \
    gdal-libs-2.3.2-8.el6.x86_64.rpm \
    mapcache-1.2.1-4.el6.x86_64.rpm \
    mapserver-6.2.2-2.el6.x86_64.rpm \
    mapserver-python-6.2.2-2.el6.x86_64.rpm \
    python2-gdal-2.3.2-8.el6.x86_64.rpm
```

Install new dependencies:

```bash
yum install -y \
    python-requests
```

With the new libraries installed, the object storage functionality is available.

As the `DatasetMetadataFileReader` has issues with recent Django versions it
needs to be disabled.

```bash
echo 'from eoxserver.core import models ; c = models.Component.objects.get(impl_id="resources.coverages.metadata.DatasetMetadataFileReader") ; c.enabled = False; c.save(); print"done"' | python /var/www/ngeo/ngeo_browse_server_instance/manage.py shell
```

This release is backwards compatible with previous versions of the Browse Server,
and all previous functionality is still available. With this release, though, it
is possible to store the optimized files of ingested browses on an OpenStack
Swift object storage.

## Steps to use or to migrate to OpenStack Swift object storage

This functionality is available for new instances created with this release of the
software, but also instances created with previous versions can be converted to
use object storages.

Conversely, it is possible to revert the usage of an object storage and use a
local disk again.

The next sections detail the options available:

  1) Create a new instance and configure the usage of the object storage or
     convert an existing Browse Server instance to use the object storage
  2) Convert an instance using an object storage back to the use of a local disk
     storage

### Create a new instance using an object storage or convert an existing one

Once the instance is set up, the object storage can be configured. For this,
the `ngeo.conf` file has to be adjusted to include the new sections and settings.
The deciding factor in the usage of the object storage is the `storage.method`
setting. If it is not set to `swift` then all subsequent configurations are
ignored.

Currently only OpenStack swift is supported.

#### Add `storage` sections to configuration

To initiate the usage of the object storage, the relevant sections need to be
filled out in the `ngeo.conf` configuration file:

```bash
[storage]
method = swift
container = <container-name>

[storage.auth]
method = swift

[storage.auth.swift]
username = <username>
password = <password>
tenant_name = <tenant-name>
tenant_id = <tenant-id>
region_name = <region-name>
auth_url = <auth-url>
```

#### Add new middleware

Additionally, this line needs to be added to the `MIDDLEWARE_CLASSES` option in
the `settings.py` configuration file:

```python
    MIDDLEWARE_CLASSES = (
        # ...
        'ngeo_browse_server.storage.middleware.AuthTokenMiddleware',
    )
```

#### Restart Browse Server

In order to commit the changes to the running system, the HTTP server needs to
be reloaded. This is done using the `service` infrastructure command:
```
service httpd graceful
```

#### Upload optimized files (only for existing instances)

Now the instance is configured for the object storage backend and every
new ingest will upload its optimized files to that configured container.

In cases when an existing instance is converted to the use of an object storage,
this configuration alone is not enough, as both the already existing optimized
files need to be transferred to the container, but also the new storage locations
need to be taken into account for the stored browses.

##### Install swift tools

In the following steps, the `swift` command line utility is required to interact
with the object storage. It is obtained by installing the python package
`python-swiftclient`. It requires Python 2.7 or greater.

If the swift tool shall be installed in the same machine as ngEO-Browse Server
Python 2.7 needs to be installed:

```bash
yum install -y centos-release-scl
yum install -y python27
```

Now the tool can be installed using the `pip` tool:

```bash
# within the Browse Server machine we need to use the SCL
scl enable python27 'pip install python_swiftclient python_keystoneclient'
```

##### Configure swift tools

As this tool provides various configuration switches it is best used by setting
environment variables to help keep the commands short:

```bash
export OS_USERNAME=<username>
export OS_PASSWORD=<password>
export OS_TENANT_NAME=<tenant-name>
export OS_TENANT_ID=<tenant-id>
export OS_AUTH_URL=https://auth.cloud.ovh.net/v3/
export OS_IDENTITY_API_VERSION=3
export OS_REGION_NAME="SERCO-DIAS1"
```

##### Upload optimized files to object storage bucket

Before starting make sure that any ingestion is stopped.

When the `swift` client is installed and the environment is set up, then the
contents of the `optimized` directory can be uploaded to an object storage container:

```bash
cd /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized/  # Check 'optimized_files_dir' in 'control.ingest' section of configuration

export BUCKET_NAME=<container-name>

scl enable python27 'swift post $BUCKET_NAME'  # create container
scl enable python27 'swift stat $BUCKET_NAME'  # check that container was created

scl enable python27 'swift upload -c --skip-identical $BUCKET_NAME *'  # perform upload

scl enable python27 'swift list --lh $BUCKET_NAME'  # Check that everything was uploaded
```

##### Adjust paths in database

Now that the optimized files are stored on the container, the paths stored in
the database need to be adjusted. To do this there is a `manage.py` command
`ngeo_upload_to_swift`. For safety purposes, there is a `--dry-run` flag which
allows to check the steps that would be taken.

```bash
python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift --dry-run
```

This command rewrites all local paths to use the `/vsiswift/` prefix that the
GDAL library understands. When the paths are deemed okay, then the actual
rewrite can be started:

```bash
python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift
```

##### Delete local optimized files

As all optimized files now reside on the object storage, it is safe to
delete the contents of the `optimized` directory.

```bash
rm -rf /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized/*
```

Now the instance is configured to use object storage and all its contents are
stored there, the migration procedure is finished.

### Reverting back to a local storage instead of an object storage

This is purely optional and for the case that an object storage is no longer
needed!

In order to no longer use an object storage, several steps have to be taken.
First the contents need to be transmitted from the object storage to the local
directory for optimized files.

As with the reverse case, the `python-swiftclient` will be used. Please refer to
the last section for prerequisites, installation and configuration. When the
setup is complete, the optimized files can be downloaded using the following
command:

```bash
scl enable python27 'swift download $BUCKET_NAME -a -D /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized/'
```

Now the configuration can be reversed by deleting or commenting out the
configuration sections described in the last section:

```
# [storage]
# method = swift
# container = <container-name>

# [storage.auth]
# method = swift

# [storage.auth.swift]
# username = <username>
# password = <password>
# tenant_name = <tenant-name>
# tenant_id = <tenant-id>
# region_name = <region-name>
# auth_url = <auth-url>
```

Now that the files are transmitted and the configuration is cleaned up, the
database references need to be adjusted to point to the local directory instead.
This can be achieved with the same management command `ngeo_upload_to_swift`
but with the `--reverse` option. Again, it is advised to perform a check using
`--dry-run` first.

```bash
python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift --reverse --dry-run
```

After thoroughly checking the paths, the actual rewriting can be done:

```bash
python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift --reverse
```

In order to update the configuration, the HTTP server has to be restarted:

```bash
service httpd restart
```

To finalize the reversion of usage of the object storage, the object storage
container can be deleted, unless it is used elsewhere:

```bash
scl enable python27 'swift delete $BUCKET_NAME'
```

