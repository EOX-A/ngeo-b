import json
from datetime import datetime

from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, utc
import requests
import logging

from ngeo_browse_server.storage.swift.conf import get_swift_auth_config
logger = logging.getLogger(__name__)


class SwiftAuthError(Exception):
    pass


def get_auth_token_and_swift_endpoint(auth_url, username, password, project_id,
                                      region_name=None, region_id=None):
    """ This method returns the auth token, its expiration time and the endpoint
        URL in one request.
        The endpoint URL is only returned when either the region name or region
        ids are provided.
        When they are provided, but no endpoint is found, an exception is raised.
    """

    headers = {'Accept': 'application/json'}
    body = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "domain": {
                            "id": "default"
                        },
                        "name": username,
                        "password": password,
                    }
                }
            },
            "scope": {
                "project": {
                    "id": project_id,
                }
            }
        }
    }

    resp = requests.post(
        '%s%s' % (auth_url, '/auth/tokens'),
        data=json.dumps(body), headers=headers
    )
    token = resp.json()['token']

    endpoint_url = None

    if region_name is not None or region_id is not None:
        # try to find the swift 'enpoints' from the provided catalogue enpoints
        for endpoints in token['catalog']:
            if endpoints['name'] == 'swift' \
                    and endpoints['type'] == 'object-store':

                # try to find the endpoint for the passed region name
                for endpoint in endpoints['endpoints']:
                    if endpoint['region'] == region_name \
                            or endpoint['region_id'] == region_id:
                        endpoint_url = endpoint['url']
                        break
                else:
                    raise SwiftAuthError(
                        "No enpoint for region '%s' found" % region_name
                    )
                break

    return (
        resp.headers['X-Subject-Token'],
        parse_datetime(token['expires_at']),
        endpoint_url,
    )


class AuthTokenManager(object):
    """ This class manages auth tokens retrieved via the Keystone API """
    def __init__(self, config=None):
        self.token = None
        self.expires = None
        self.storage_url = None

        config = config or get_swift_auth_config()

        self.auth_url = config['auth_url']
        self.username = config['username']
        self.password = config['password']
        self.tenant_id = config['tenant_id']
        self.region_name = config['region_name']
        self.region_id = config['region_id']

    def _refresh_token(self):
        utcnow = make_aware(datetime.utcnow(), utc)
        if not self.expires or utcnow >= self.expires:
            items = get_auth_token_and_swift_endpoint(
                self.auth_url,
                self.username,
                self.password,
                self.tenant_id,
                self.region_name,
                self.region_id,
            )
            self.token, self.expires, self.storage_url = items

    def get_auth_token(self):
        self._refresh_token()
        return self.token

    def get_storage_url(self):
        self._refresh_token()
        return self.storage_url
