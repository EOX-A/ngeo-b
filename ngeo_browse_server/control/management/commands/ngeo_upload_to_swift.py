# ------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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
# -----------------------------------------------------------------------------

import logging
from optparse import make_option
import os.path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from eoxserver.backends import models as backends

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.control.management.commands import LogToConsoleMixIn
from ngeo_browse_server.storage.conf import get_auth_method, get_storage_url
from ngeo_browse_server.control.ingest.config import (
    INGEST_SECTION, get_project_relative_path
)


logger = logging.getLogger(__name__)


class Command(LogToConsoleMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', action="store_true",
            dest='dry_run', default=False,
            help=("Optional switch to only print times without actually "
                  "(re)seeding.")
        ),
        make_option('--reverse', action="store_true",
            dest='reverse', default=False,
            help=("Optional. Do the rervse: use local paths instead of on the "
                  "object storage.")
        ),
    )

    help = (
        "Upload all preprocessed images of a browse layer to a OpenStack "
        "swift object storage."
    )

    def handle(self, *browse_layer_id, **kwargs):
        # parse command arguments
        self.verbosity = int(kwargs.get("verbosity", 1))
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], self.verbosity, traceback)

        dry_run = kwargs['dry_run']
        reverse = kwargs['reverse']

        conf = get_ngeo_config()

        if not reverse:
            storage_url = get_storage_url(conf)
            method = get_auth_method(conf)
            if method != 'swift':
                raise CommandError('Auth method not set to swift')

            if not storage_url:
                raise CommandError('No storage URL given')

            local_paths = backends.LocalPath.objects.exclude(
                path__startswith='/vsiswift'
            )
            new_base_dir = '/vsiswift'

        else:
            # retrieve from object storage instead
            local_paths = backends.LocalPath.objects.filter(
                path__startswith='/vsiswift'
            )
            new_base_dir = get_project_relative_path(
                conf.get(INGEST_SECTION, "optimized_files_dir")
            )

        count = local_paths.count()

        logger.info('Adjusting %d files' % count)
        with transaction.commit_on_success():
            for local_path in local_paths:
                path = local_path.path
                new_path = os.path.join(new_base_dir, *path.split('/')[-3:])

                if dry_run:
                    logger.info("%s -> %s " % (local_path, new_path))

                else:
                    local_path.path = new_path
                    local_path.save()

        logger.info('Done adjusting %d files' % count)
