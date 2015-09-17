import re

from django.db import models
from django.test import TestCase

from edc_audit.audit_trail import AuditTrail
from edc_base.model.models.base_uuid_model import BaseUuidModel


class TestAuditedModel(models.Model):

    field1 = models.CharField(max_length=10)

    history = AuditTrail()

    class Meta:
        app_label = 'edc_audit'


class TestAuditedUuidModel(BaseUuidModel):

    field1 = models.CharField(max_length=10)

    history = AuditTrail()

    class Meta:
        app_label = 'edc_audit'


class TestAudit(TestCase):

    def test_creates_audit_record(self):
        test_audited_model = TestAuditedModel(field1='erik')
        test_audited_model.save()
        self.assertEqual(test_audited_model.history.all().count(), 1)

    def test_updates_audit_record(self):
        test_audited_model = TestAuditedModel(field1='erik')
        test_audited_model.save()
        test_audited_model.save()
        self.assertEqual(test_audited_model.history.all().count(), 2)

    def test_creates2_audit_record(self):
        test_audited_model = TestAuditedModel.objects.create(field1='erik')
        self.assertEqual(test_audited_model.history.all().count(), 1)

    def test_audit_record(self):
        test_audited_model = TestAuditedModel.objects.create(field1='erik')
        self.assertEqual(test_audited_model.history.filter(field1='erik').count(), 1)

    def test_audit_record_uuid(self):
        test_audited_model = TestAuditedUuidModel.objects.create(field1='erik')
        self.assertEqual(test_audited_model.history.filter(field1='erik').count(), 1)

    def test_audit_record_uuid2(self):
        test_audited_model = TestAuditedUuidModel.objects.create(field1='erik')
        pk = test_audited_model.pk
        regex = re.compile('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}')
        self.assertTrue(re.match(regex, pk))
        self.assertEqual(test_audited_model.history.filter(field1='erik').count(), 1)
