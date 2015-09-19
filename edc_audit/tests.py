import re

from django.db import models
from django.test import TestCase

from edc_audit.audit_trail import AuditTrail
from edc_base.model.models.base_uuid_model import BaseUuidModel
from django.core import serializers


class Transaction(models.Model):

    tx = models.CharField(max_length=100)

    class Meta:
        app_label = 'edc_audit'


class SyncModel(models.Model):

    def serialize(self, sender, instance, raw, created, using, **kwargs):
        tx = serializers.serialize("json", [instance, ], ensure_ascii=False, use_natural_keys=False)
        Transaction.objects.create(tx=tx)

    def _deserialize_post(self):
        pass


class TestAuditedSyncModel(SyncModel):

    field1 = models.CharField(max_length=10)

    history = AuditTrail()

    class Meta:
        app_label = 'edc_audit'


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

    def test_serialize_called_in_signal(self):
        test_audited_model = TestAuditedSyncModel.objects.create(field1='erik')
        self.assert_(test_audited_model.history.model.serialize)
        self.assert_(test_audited_model.history.model._deserialize_post)
        self.assertEqual(Transaction.objects.count(), 1)
