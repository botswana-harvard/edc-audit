from django.db.models import get_models
from django.core.management.base import LabelCommand
from django.db import connection, transaction


class Command(LabelCommand):

    help = 'Verify all edc_audit models have the required fields.'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        for model in get_models():
            table_name = model._meta.__dict__.get('db_table')
            if '_audit' in table_name and 'audit_trail' not in table_name:
                print 'checking {0}'.format(table_name)
                try:
                    cursor.execute("ALTER TABLE {0} add column `_audit_subject_identifier` varchar(50)".format(table_name))
                    transaction.commit_unless_managed()
                    print '**Altered table {0}'.format(table_name)
                except:
                    pass
