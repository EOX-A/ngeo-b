
from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.storage.conf import (
    get_storage_method, get_swift_container
)

from ngeo_browse_server.storage.swift.auth import AuthTokenManager
from ngeo_browse_server.storage.swift.manager import SwiftFileManager


def get_file_manager(config=None):
    config = config or get_ngeo_config()

    storage_method = get_storage_method(config)
    if not storage_method:
        return None
    elif storage_method == 'swift':
        return SwiftFileManager(
            get_swift_container(config),
            AuthTokenManager()
        )
    else:
        raise Exception("Unsupported storage method '%s'" % storage_method)
