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
from osgeo import gdal

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.storage.conf import (
    get_auth_method, get_storage_url
)
from ngeo_browse_server.storage.swift.auth import AuthTokenManager


class AuthTokenMiddleware(object):
    """ Django middleware class to handle auth token retrieval. Currently only
        for swift.
    """
    def __init__(self):
        conf = get_ngeo_config()
        self.storage_url = get_storage_url(conf)
        method = get_auth_method(conf)
        if self.storage_url and method == 'swift':
            self.manager = AuthTokenManager(
                # **get_swift_auth_config(conf)
            )
        elif method is not None:
            raise NotImplementedError(
                'Auth method %s is not implmented' % method
            )
        else:
            self.manager = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        # check if we actually need to process the request
        if view_func != ows_view or self.manager is None:
            return None

        os.environ['SWIFT_AUTH_TOKEN'] = self.manager.get_auth_token()
        os.environ['SWIFT_STORAGE_URL'] = self.storage_url

        # needs to be done for seeding, so probably for OWS as-well
        gdal.VSICurlClearCache()

        return None
