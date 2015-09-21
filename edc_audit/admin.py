from django.contrib import admin

from edc_base.modeladmin.admin import BaseModelAdmin


class AuditModelAdmin(admin.ModelAdmin):

    date_hierarchy = 'created'
    search_fields = ('audit_subject_identifier')
    list_display = ('audit_subject_identifier', 'audit_id', 'app_label', 'model_name',)
    list_filter = ('created', 'modified', 'user_created', 'user_modified', 'hostname_created', 'hostname_modified')


class AuditCommentAdmin(BaseModelAdmin):

    list_filter = ('audit_subject_identifier', 'app_label', 'model_name', )
    list_display = ('audit_subject_identifier', 'audit_id', 'app_label', 'model_name',)

# admin.site.register(AuditComment, AuditCommentAdmin)
