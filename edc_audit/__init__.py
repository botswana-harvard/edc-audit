from django.db import models
from django import get_version
from .helper import get_subject_identifier

if not get_version().startswith('1.6'):
    raise ImportError('edc_audit is not compatible with this version of django. Use simple_history.')


# Populate the fields that every Audit model in this project will use.
GLOBAL_TRACK_FIELDS = (
    ('_audit_subject_identifier', models.CharField(max_length=50, null=True), get_subject_identifier),
    # ('_audit_comment', models.CharField(max_length=250, null=True, blank=True), ''),
)
