from django.contrib import admin

from edc_base.utils import convert_from_camel


class BaseAuditModelAdmin(admin.ModelAdmin):

    def __init__(self, *args, **kwargs):
        model_cls = args[0]
        super(BaseAuditModelAdmin, self).__init__(*args, **kwargs)
        self.search_fields = ['_audit_subject_identifier', 'id', 'revision']
        if 'registered_subject' in dir(model_cls):
            self.search_fields = ['registered_subject__subject_identifier'] + self.search_fields
        elif 'appointment' in dir(model_cls):
            self.search_fields = ['appointment__registered_subject__subject_identifier'] + self.search_fields
        elif 'visit_model' in dir(model_cls):
            self.search_fields = [
                '{0}__appointment__registered_subject__subject_identifier'.format(
                    convert_from_camel(model_cls._meta.object_name).split('_audit')[0])] + self.search_fields
        self.readonly_fields = [field.name for field in model_cls._meta.fields]

    date_hierarchy = '_audit_timestamp'
    list_display = ('_audit_id', '_audit_subject_identifier', '_audit_change_type', '_audit_timestamp',
                    'created', 'modified', 'user_created', 'user_modified', 'hostname_created',
                    'hostname_modified')
    list_filter = ('_audit_change_type', '_audit_timestamp', 'created', 'modified', 'user_created',
                   'user_modified', 'hostname_created', 'hostname_modified')
    # search_fields = ('_audit_subject_identifier', '_audit_id')


class AuditModelAdmin(admin.ModelAdmin):

    date_hierarchy = 'created'
    search_fields = ('audit_subject_identifier')
    list_display = ('audit_subject_identifier', 'audit_id', 'app_label', 'model_name',)
    list_filter = ('created', 'modified', 'user_created', 'user_modified', 'hostname_created', 'hostname_modified')


class AuditCommentAdmin(admin.ModelAdmin):

    list_filter = ('audit_subject_identifier', 'app_label', 'model_name', )
    list_display = ('audit_subject_identifier', 'audit_id', 'app_label', 'model_name',)

# admin.site.register(AuditComment, AuditCommentAdmin)
