#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2019 European Space Agency
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


# Migration procedure


#-------------------------------------------------------------------------------
# Steps to migrate ngEO_Browse_Server version <2.1.0 to 2.1.0
#-------------------------------------------------------------------------------
# The steps assume a default installation and configuration as for
# example provided via the `ngeo-install.sh` script.


To enable the cloud storage functionality, GDAL and all dependent packages need
to be updated. The RPMs are available with the new installation script. In order
to delete the old versions of GDAL and dependencies, the following command needs
to be run:

```
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

Now the next command installs the new RPM files.

```
    yum install \
        EOxServer-0.3.7-1.x86_64.rpm \
        gdal-2.3.2-8.el6.x86_64.rpm \
        gdal-libs-2.3.2-8.el6.x86_64.rpm \
        mapcache-1.2.1-4.el6.x86_64.rpm \
        mapserver-6.2.2-2.el6.x86_64.rpm \
        mapserver-python-6.2.2-2.el6.x86_64.rpm \
        python2-gdal-2.3.2-8.el6.x86_64.rpm
```

With the new libraries installed, the object storage functionality is available.

As the `DatasetMetadataFileReader` has issues with recent Django versions it
needs to be disabled. 

```
echo 'from eoxserver.core import models ; c = models.Component.objects.get(impl_id="resources.coverages.metadata.DatasetMetadataFileReader") ; c.enabled = False; c.save(); print"done"' | python /var/www/ngeo/ngeo_browse_server_instance/manage.py shell
```


This release is backwards compatible with previous setups of ngEO Browse Server,
and all previous functionality is still available. With this release, though, it
is possible to store the optimized files of ingested browses on an OpenStack
Swift objectstorage.

This functionality is available for instances created with this release of the
software, but also instances created with previous versions can be converted to
use object storages.

Conversely, it is possible to revert the usage of an object storage and use a
local disk again.

The next sections detail the options available:

  1) Create a new instance and configure the usage of the object storage or
     convert an existing browse server instance to use the object storage
  2) Convert an instance using an object storage back to the use of a loca disk
     storage


# Create a new instance using an object storage or convert a new existing one


When the instance was set up, the object storage can be configured. For this,
the ngeo.conf file has to be adjusted to include the new sections and settings.
The deciding factor in the usage of the object storage is the `storage_url`
setting. If not present, all subsequent configurations are ignored.

Currently only OpenStack swift is supported.


To initiate the usage of the object storage, the relevant sections need to be
filled out in the ngeo.conf configuration file:
```
    [storage]
    storage_url = <storage-url>
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


Add the appropriate middleware to the settings.py file:



Additionally, this line needs to be added to the `MIDDLEWARE_CLASSES` option in
the settings.py configuration file:
```
    MIDDLEWARE_CLASSES = (
        # ...
        'ngeo_browse_server.storage.middleware.AuthTokenMiddleware',
    )
```

In order to commit the changes to the running system, the HTTP server needs to
be reloaded. This is done unsing the `service` infrastructure command:
```
service httpd graceful
```

Now the instance is configured for the of the object storage backend and every
new ingest will upload its optimized files to that configured container.

In cases when an existing instance is converted to the use of an object storage,
this configuration alone is not enough, as both the already existing optimized
files need to be transferred to the container, but also the new storage locations
need to be taken into account for the stored browses.

The next step is to copy the optimized files to the container. This is best done
by using the `python-swiftclient` package. It requires version 2.7 or greater
and can be installed using the `pip` tool:

```
    pip install python_swiftclient python_keystoneclient
```

As this tool provides various configuration switches it is best used by setting
environment variables to help keep the commands short:

```
    export OS_USERNAME=<username>
    export OS_PASSWORD=<password>
    export OS_TENANT_NAME=<tenant-name>
    export OS_TENANT_ID=<tenant-id>
    export OS_REGION_NAME=<region-name>
    export OS_AUTH_URL=<auth-url>
    export AUTH_VERSION=3
    export OS_IDENTITY_API_VERSION=3
```

When the `swift` client is installed an the environment is set up, then the
contents of the `optimized` directory can be uploaded to the container:

```
    # go to the optimized files directory:
    cd /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized/

    # use e.g: python-swiftclient
    swift upload '<container-name>' *
```

To assert that the files are correctly uploaded, the `list` subcommand can be
used to check the files:

```
    swift list <container>
```

Now that the optimized files are stored on the container, the paths stored in
the database can be adjusted. To do this there is a `manade.py` command
`ngeo_upload_to_swift`. For safety purposes, there is a `--dry-run` flag which
allows to check the steps that would be taken.

```
    python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift --dry-run
```

This command rewrites all local paths to use the `/vsiswift/` prefix that the
GDAL library understands. When the paths are deemed okay, then the actual
rewrite can be started:

```
    python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift
```

As all optimized files now reside on the object storage, it is now safe to
delete the contents of the `optimized` directory.

```
    rm -rf /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized/*
```


Now the instance is confiugred for the object storage and all its contents are
stored there, the migration procedure is finished.


# Transferring files to a local storage instead of an object storage:

This is purely optional and for the case that an object storage is no longer
needed!

In order to no longer use an object storage, several steps have to be taken.
First the contents need to be transmitted from the object storage to the local
directory for optimized files.

As with the reverse case, the `python-swiftclient` will be used. Please refer to
the last section for prerequisites, installation and configuration. When the
setup is complete, the optimized files can be downloaded using the following
command:

```
    swift download '<container-name>' -a -D /var/www/ngeo/ngeo_browse_server_instance/ngeo_browse_server_instance/data/optimized/
```


Now the configuration can be reversed by deleting or commenting out the
configuration sections described in the last section:

```
    # [storage]
    # storage_url = <storage-url>
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
database references can be adjusted to point to the local directory instead.
This can be achieved with the same management command `ngeo_upload_to_swift`
but with the `--reverse` option. Again, it is advised to perform a check using 
`--dry-run` first.

```
    python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift --reverse --dry-run
```

After thoroughly checking the paths the actual rewriting can be done:

```
    python /var/www/ngeo/ngeo_browse_server_instance/manage.py ngeo_upload_to_swift --reverse
```

In order to update the configuration, the HTTP server has to be restarted:
```
    service httpd restart
```

To finalize the reversion of usage of the object storage, the object storage
container can be deleted, unless it is used elsewhere:
```
    swift delete '<container-name>'
```

