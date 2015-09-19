from django.db import models
from django import get_version

if not get_version().startswith('1.6'):
    raise ImportError('edc_audit is not compatible with this version of django. Use simple_history.')


def get_subject_identifier(obj):
    """Returns the subject identifier from the model instance.

    If subject_identifier is not a field, have the model class
    return the subject_identifier from method `get_subject_identifier`.
    """
    try:
        subject_identifier = obj.subject_identifier
    except AttributeError:
        try:
            subject_identifier = obj.get_subject_identifier()
        except AttributeError:
            subject_identifier = None
    return subject_identifier


# Populate the fields that every Audit model in this project will use.
GLOBAL_TRACK_FIELDS = (
    ('_audit_subject_identifier', models.CharField(max_length=50, null=True), get_subject_identifier),
    # ('_audit_comment', models.CharField(max_length=250, null=True, blank=True), ''),
)
