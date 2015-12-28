from django.db import models

from edc_base.model.models import BaseUuidModel


class AuditComment (BaseUuidModel):

    app_label = models.CharField(
        max_length=35,
    )

    model_name = models.CharField(
        max_length=50,
    )

    audit_subject_identifier = models.CharField(
        max_length=50,
    )

    audit_id = models.CharField(max_length=50)

    audit_code = models.CharField(
        max_length=25,
    )

    audit_comment = models.TextField(
        max_length=250,
        help_text='Add a comment describing the reason for the data change.'
    )

    def __unicode__(self):
        return self.audit_comment[0:50]

    class Meta:
        app_label = 'edc_audit'
        ordering = ['created']
