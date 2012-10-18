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
        ),
    )
    
    args = 'browse-report-xml-file1 [browse-report-xml-file2] ... >'
    help = 'Ingests the specified ngEO Browse Reports.'

    def handle(self, *filenames, **kwargs):
        if not len(filenames):
            raise CommandError("No input files given.")
        with transaction.commit_manually():
            for filename in filenames:
                sid = transaction.savepoint()
                try:
                    document = etree.parse(filename)
                    ingest_browse_report(document)
                except Exception, e:
                    on_error = kwargs["on_error"]
                    if on_error == "continue":
                        # TODO: write warning
                        transaction.savepoint_rollback(sid)
                    elif on_error == "stop":
                        transaction.savepoint_rollback(sid)
                        transaction.commit()
                        raise
                    elif on_error == "rollback":
                        transaction.rollback()
                        raise
                
                transaction.savepoint_commit(sid)
            
            transaction.commit()
