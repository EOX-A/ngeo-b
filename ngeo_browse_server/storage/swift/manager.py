import os

from os.path import basename, join
import shutil

from osgeo import gdal
import requests
# from urlparse import urljoin


def upload_file(storage_url, container, prefix, file_, auth_token,
                filename=None, replace=False):
    if isinstance(file_, basestring):
        file_ = open(file_)

    filename = filename or file_.name

    headers = {"X-Auth-Token": auth_token}
    path = join(prefix, basename(filename))

    url = "%s/%s/%s" % (storage_url, container, path)
    resp = requests.head(url, headers=headers)

    if resp.status_code == 200:
        if replace:
            delete_file(storage_url, container, path)
        else:
            raise Exception("File at path '%s' already exists" % path)

    resp = requests.put(url, data=file_, headers=headers)
    if resp.status_code != 201:
        raise Exception(
            "Upload of file '%s' to %s failed, message: %s" % (
                filename, url, resp.text
            )
        )


def delete_file(storage_url, container, path, auth_token):
    headers = {"X-Auth-Token": auth_token}
    url = "%s/%s/%s" % (storage_url, container, path)
    resp = requests.delete(url, headers=headers)

    if resp.status_code >= 300:
        raise Exception("Failed to delete file '%s'" % path)


def list_contents(storage_url, container, prefix_path, auth_token):
    headers = {"X-Auth-Token": auth_token}
    url = "%s/%s" % (storage_url, container)
    resp = requests.get(url, params={
        "prefix": prefix_path,
        "format": "json",
    }, headers=headers)

    if resp.status_code != 200:
        raise Exception("Failed to list contents of container '%s'" % container)

    contents = resp.json()
    return [
        item["name"]
        for item in contents
        if item["content_type"] != "application/x-directory"
    ]


def download_file(storage_url, container, path, local_path, auth_token):
    headers = {"X-Auth-Token": auth_token}
    url = "%s/%s/%s" % (storage_url, container, path)
    resp = requests.get(url, headers=headers, stream=True)

    if resp.status_code != 200:
        raise Exception("Failed to download file '%s'" % path)

    with open(local_path, 'wb') as out_file:
        shutil.copyfileobj(resp.raw, out_file)


class SwiftFileManager(object):
    """
    """
    def __init__(self, container, auth_manager, storage_url=None, retries=3):
        self.container = container
        self.auth_manager = auth_manager
        self.storage_url = storage_url
        self.retries = retries

    def prepare_environment(self):
        os.environ['SWIFT_AUTH_TOKEN'] = self.auth_manager.get_auth_token()
        os.environ['SWIFT_STORAGE_URL'] = (
            self.storage_url or self.auth_manager.get_storage_url()
        )
        gdal.VSICurlClearCache()

    def get_vsi_filename(self, path):
        return '/vsiswift/%s/%s' % (self.container, path)

    def retry(self, func, get_args):
        """ Retrying wrapper function.
        """
        for i in range(self.retries):
            try:
                return func(*get_args())
            except:
                pass
        raise

    def upload_file(self, prefix, file_, filename=None, replace=None):
        return self.retry(
            upload_file,
            lambda: (
                self.storage_url or self.auth_manager.get_storage_url(),
                self.container,
                prefix, file_,
                self.auth_manager.get_auth_token(), filename, replace
            ),
        )

    def delete_file(self, path):
        if path.startswith('/vsiswift'):
            path = '/'.join(path.split('/')[2:])

        return self.retry(
            delete_file,
            lambda: (
                self.storage_url or self.auth_manager.get_storage_url(),
                self.container,
                path,
                self.auth_manager.get_auth_token()
            ),
        )

    def list_contents(self, prefix_path):
        return self.retry(
            list_contents,
            lambda: (
                self.storage_url or self.auth_manager.get_storage_url(),
                self.container,
                prefix_path,
                self.auth_manager.get_auth_token()
            ),
        )

    def download_file(self, path, local_path):
        if path.startswith('/vsiswift'):
            path = '/'.join(path.split('/')[2:])

        return self.retry(
            download_file,
            lambda: (
                self.storage_url or self.auth_manager.get_storage_url(),
                self.container,
                path,
                local_path,
                self.auth_manager.get_auth_token()
            ),
        )
