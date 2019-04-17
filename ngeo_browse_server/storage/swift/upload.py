

from os.path import basename

import requests
# from urlparse import urljoin


def upload_file(storage_url, container, file_, auth_token, replace=False):
    if isinstance(file_, basestring):
        file_ = open(file_)

    headers = {"X-Auth-Token": auth_token}

    url = "%s/%s/%s" % (storage_url, container, basename(file_.name))
    response = requests.head(url, headers=headers)

    if response.status_code == 200:
        # TODO: send delete request
        pass

    # TODO: retry upload, especially for larger ones

    resp = requests.put(url, data=file_, headers=headers)
    if resp.status_code != 201:
        raise Exception(
            "Upload of file '%s' to %s failed, message: %s" % (
                file_.name, url, resp.text
            )
        )
