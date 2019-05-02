import json
from datetime import datetime

from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, utc
import requests
import logging

from ngeo_browse_server.storage.swift.conf import get_swift_auth_config
logger = logging.getLogger(__name__)


def get_auth_token(auth_url, username, password, project_id):
    """
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
    # logger.info(resp.text)
    return (
        resp.headers['X-Subject-Token'],
        parse_datetime(resp.json()['token']['expires_at'])
    )


class AuthTokenManager(object):
    def __init__(self, config=None):
        self.token = None
        self.expires = None

        config = config or get_swift_auth_config()

        self.auth_url = config['auth_url']
        self.username = config['username']
        self.password = config['password']
        self.tenant_id = config['tenant_id']

    def _refresh_token(self):
        self.token, self.expires = get_auth_token(
            self.auth_url,
            self.username,
            self.password,
            self.tenant_id,
        )

    def get_auth_token(self):
        utcnow = make_aware(datetime.utcnow(), utc)
        if not self.expires or utcnow >= self.expires:
            self._refresh_token()

        return self.token
