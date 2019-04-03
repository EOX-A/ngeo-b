# ------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

import os

from eoxserver.services.views import ows as ows_view
from keystoneclient.v3 import client


from ngeo_browse_server.config import (
    get_ngeo_config, safe_get
)


STORAGE_SECTION = 'storage'
AUTH_SECTION = 'storage.auth'
SWIFT_SECTION = 'storage.auth.swift'


def get_auth_method(conf=None):
    conf = conf or get_ngeo_config()
    return safe_get(conf, AUTH_SECTION, 'method', None)


def get_swift_auth_config(conf=None):
    conf = conf or get_ngeo_config()

    return {
        'username': safe_get(conf, SWIFT_SECTION, 'username'),
        'password': safe_get(conf, SWIFT_SECTION, 'password'),
        'tenant_name': safe_get(conf, SWIFT_SECTION, 'password'),
        'tenant_id': safe_get(conf, SWIFT_SECTION, 'tenant_id'),
        'auth_url': safe_get(conf, SWIFT_SECTION, 'auth_url'),
        'user_id': safe_get(conf, SWIFT_SECTION, 'user_id'),
        'user_domain_name': safe_get(conf, SWIFT_SECTION, 'user_domain_name'),
        'user_domain_id': safe_get(conf, SWIFT_SECTION, 'user_domain_id'),
        'project_name': safe_get(conf, SWIFT_SECTION, 'project_name'),
        'project_id': safe_get(conf, SWIFT_SECTION, 'project_id'),
        'project_domain_name': safe_get(
            conf, SWIFT_SECTION, 'project_domain_name'
        ),
        'project_domain_id': safe_get(conf, SWIFT_SECTION, 'project_domain_id'),
        'insecure': False,
        'timeout':  safe_get(conf, SWIFT_SECTION, 'timeout'),
    }


class AuthTokenMiddleware(object):
    """ Django middleware class to handle auth token retrieval. Currently only
        for swift.
    """
    def __init__(self):
        conf = get_ngeo_config()
        self.storage_url = safe_get(conf, STORAGE_SECTION, 'storage_url')
        method = get_auth_method(conf)
        if self.storage_url and method == 'swift':
            self.client = client.Client(
                **get_swift_auth_config(conf)
            )
        elif method is not None:
            raise NotImplementedError(
                'Auth method %s is not implmented' % method
            )
        else:
            self.client = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        # check if we actually need to process the request
        if view_func != ows_view or self.client is None:
            return None

        os.environ['SWIFT_AUTH_TOKEN'] = self.client.auth_token
        os.environ['SWIFT_STORAGE_URL'] = self.storage_url

        return None
