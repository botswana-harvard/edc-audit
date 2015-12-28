import re

from django.db import models
from django.test import TestCase

from edc_audit.audit_trail import AuditTrail
from edc_base.model.models import BaseUuidModel
from edc_sync.models import SyncModelMixin
from edc_sync.models.outgoing_transaction import OutgoingTransaction
from django.test.utils import override_settings


class Transaction(models.Model):

    tx = models.CharField(max_length=100)

    class Meta:
        app_label = 'edc_audit'


class TestManager(models.Manager):

    def get_by_natural_key(self, field1):
        return self.get(field1=field1)


class TestAuditedSyncModel(SyncModelMixin, BaseUuidModel):

    field1 = models.CharField(max_length=10, unique=True)

    objects = TestManager()

    history = AuditTrail()

    def natural_key(self):
        return (self.field1, )

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

    @override_settings(ALLOW_MODEL_SERIALIZATION=True)
    def test_audit_class_has_attrs(self):
        test_audited_model = TestAuditedSyncModel.objects.create(field1='erik')
        self.assert_(test_audited_model.history.model.to_outgoing_transaction)
        self.assert_(test_audited_model.history.model.is_serialized)
        self.assert_(test_audited_model.history.model.natural_key)
        self.assert_(test_audited_model.history.model.objects.get_by_natural_key)
        self.assertTrue(test_audited_model.history.model().is_serialized())

    @override_settings(ALLOW_MODEL_SERIALIZATION=True)
    def test_serialize_called_in_signal(self):
        obj = TestAuditedSyncModel.objects.create(field1='erik')
        self.assertEqual(OutgoingTransaction.objects.filter(tx_name='TestAuditedSyncModel').count(), 1)
        self.assertEqual(OutgoingTransaction.objects.filter(tx_name='TestAuditedSyncModelAudit').count(), 1)
        obj.save()
        self.assertEqual(OutgoingTransaction.objects.filter(
            tx_name='TestAuditedSyncModel',
            action='I').count(), 1)
        self.assertEqual(OutgoingTransaction.objects.filter(
            tx_name='TestAuditedSyncModel',
            action='U').count(), 1)
        # audit is always a new instance
        self.assertEqual(OutgoingTransaction.objects.filter(
            tx_name='TestAuditedSyncModelAudit',
            action='I',).count(), 2)
