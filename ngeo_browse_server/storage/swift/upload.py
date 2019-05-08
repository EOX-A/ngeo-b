

from os.path import basename, join

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


class SwiftFileManager(object):
    """
    """
    def __init__(self, storage_url, container, auth_manager):
        self.storage_url = storage_url
        self.container = container
        self.auth_manager = auth_manager

    def retry(self, func, get_args, retries=3):
        """ Retrying wrapper function.
        """
        for i in range(retries):
            try:
                return func(*get_args())
            except:
                pass
        raise

    def upload_file(self, prefix, file_, filename=None, replace=None, retries=3):
        return self.retry(
            upload_file,
            lambda: (
                self.storage_url, self.container, prefix, file_,
                self.auth_manager.get_auth_token(), filename, replace
            ),
            retries
        )

    def delete_file(self, path, retries=3):
        return self.retry(
            delete_file,
            lambda: (
                self.storage_url, self.container, path,
                self.auth_manager.get_auth_token()
            ),
            retries
        )

    def list_contents(self, prefix_path, retries=3):
        return self.retry(
            list_contents,
            lambda: (
                self.storage_url, self.container, prefix_path,
                self.auth_manager.get_auth_token()
            ),
            retries
        )
