from lxml import etree
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ngeo_browse_server.control.ingest import ingest_browse_report



class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--on-error',
            dest='on_error', default="rollback",
            choices=["continue", "stop", "rollback"],
            help="Declare how errors shall be handled. Default is 'rollback'."
        )
    )
    
    args = '< browse-report-xml-file browse-report-xml-file ... >'
    help = 'Ingests the specified ngEO Browse Reports.'

    def handle(self, on_error, *filenames):
        with transaction.commit_manually():
            for filename in filenames:
                sid = transaction.savepoint()
                try:
                    document = etree.parse(filename)
                    ingest_browse_report(document)
                except Exception, e:
                    if on_error == "continue":
                        # TODO: write warning
                        transaction.savepoint_rollback(sid)
                    elif on_error == "stop":
                        transaction.savepoint_rollback(sid)
                        transaction.commit()
                        raise CommandError(str(e))
                    elif on_error == "rollback":
                        transaction.rollback()
                        raise CommandError(str(e))
