""" https://github.com/LaundroMat/django-AuditTrail/blob/master/audit.py """
import copy
import datetime
import json
import re


from django import get_version
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from edc_base.model.fields import UUIDAutoField, UUIDField

from edc_audit import GLOBAL_TRACK_FIELDS

from .admin import BaseAuditModelAdmin

value_error_re = re.compile("^.+'(.+)'$")

if not get_version().startswith('1.6'):
    raise ImportError('This module is for 1.6 only')


class AuditTrailError(Exception):
    pass


class AuditTrail(object):
    def __init__(self, show_in_admin=False, save_change_type=True, audit_deletes=True,
                 track_fields=None):
        self.opts = {}
        self.opts['show_in_admin'] = False  # show_in_admin
        self.opts['save_change_type'] = save_change_type
        self.opts['audit_deletes'] = audit_deletes
        if track_fields:
            self.opts['track_fields'] = track_fields
        else:
            self.opts['track_fields'] = []

    def contribute_to_class(self, cls, name):
        # This should only get added once the class is otherwise complete
        def _contribute(sender, **kwargs):
            model = create_audit_model(sender, **self.opts)
            if self.opts['show_in_admin']:
                # Enable admin integration
                # If ModelAdmin needs options or different base class, find
                # some way to make the commented code work
                cls_admin_name = model.__name__ + 'Admin'
                clsAdmin = type(cls_admin_name, (BaseAuditModelAdmin, ), {model: model})
                admin.site.register(model, clsAdmin)
                # Otherwise, register class with default ModelAdmin
                # admin.site.register(model, AuditModelAdmin)
            descriptor = AuditTrailDescriptor(model._default_manager, sender._meta.pk.attname)
            setattr(sender, name, descriptor)

            def _audit_track(instance, field_arr, **kwargs):
                field_name = field_arr[0]
                try:
                    return getattr(instance, field_name)
                except AttributeError:
                    if len(field_arr) > 2:
                        if callable(field_arr[2]):
                            fn = field_arr[2]
                            return fn(instance)
                        else:
                            return field_arr[2]

            def _audit(sender, instance, raw, created, using, **kwargs):
                if not raw:
                    # Write model changes to the audit model.
                    # instance is the current (non-audit) model.
                    kwargs = {}
                    for field in sender._meta.fields:
                        try:
                            # slip hash in to silence encryption
                            value = getattr(instance, field.name)
                            if isinstance(value, datetime.date):
                                value = json.dumps(value, cls=DjangoJSONEncoder)
                            if not field.field_cryptor.is_encrypted(value):
                                kwargs[field.name] = field.field_cryptor.get_hash_with_prefix(value)
                            else:
                                kwargs[field.name] = value
                        except AttributeError:
                            try:
                                kwargs[field.name] = getattr(instance, field.name)
                            except instance.DoesNotExist:
                                kwargs[field.name] = None
                    if self.opts['save_change_type']:
                        if created:
                            kwargs['_audit_change_type'] = 'I'
                        else:
                            kwargs['_audit_change_type'] = 'U'
                    for field_arr in model._audit_track:
                        kwargs[field_arr[0]] = _audit_track(instance, field_arr)
                    model._default_manager.create(**kwargs)

            models.signals.post_save.connect(
                _audit, sender=cls, weak=False,
                dispatch_uid='audit_on_save_{0}'.format(model._meta.object_name.lower()))

            if self.opts['audit_deletes']:
                def _audit_delete(sender, instance, **kwargs):
                    # Write model changes to the edc_audit model
                    kwargs = {}
                    for field in sender._meta.fields:
                        kwargs[field.name] = getattr(instance, field.name)
                    if self.opts['save_change_type']:
                        kwargs['_audit_change_type'] = 'D'
                    for field_arr in model._audit_track:
                        kwargs[field_arr[0]] = _audit_track(instance, field_arr)
                    model._default_manager.create(**kwargs)
                # Uncomment this line for pre r8223 Django builds
                # dispatcher.connect(_audit_delete, signal=models.signals.pre_delete, sender=cls, weak=False)
                # Comment this line for pre r8223 Django builds
                models.signals.pre_delete.connect(
                    _audit_delete, sender=cls, weak=False,
                    dispatch_uid='audit_delete_{0}'.format(model._meta.object_name.lower()))

        #  Uncomment this line for pre r8223 Django builds
        # dispatcher.connect(_contribute, signal=models.signals.class_prepared, sender=cls, weak=False)
        # Comment this line for pre r8223 Django builds
        models.signals.class_prepared.connect(_contribute, sender=cls, weak=False)


class AuditTrailDescriptor(object):
    def __init__(self, manager, pk_attribute):
        self.manager = manager
        self.pk_attribute = pk_attribute

    def __get__(self, instance=None, owner=None):
        if not instance:
            # raise AttributeError, "Audit trail is only accessible via %s instances." % type.__name__
            return create_audit_manager_class(self.manager)
        else:
            return create_audit_manager_with_pk(self.manager, self.pk_attribute, instance._get_pk_val())

    def __set__(self, instance, value):
        raise AttributeError("Audit trail may not be edited in this manner.")


def create_audit_manager_with_pk(manager, pk_attribute, pk):
    """Create an audit trail manager based on the current object"""
    class AuditTrailWithPkManager(manager.__class__):
        def __init__(self, *arg, **kw):
            super(AuditTrailWithPkManager, self).__init__(*arg, **kw)
            self.model = manager.model

        def get_query_set(self):
            qs = super(AuditTrailWithPkManager, self).get_query_set().filter(**{pk_attribute: pk})
            if self._db is not None:
                qs = qs.using(self._db)
            return qs
    return AuditTrailWithPkManager()


def create_audit_manager_class(manager):
    """Create an audit trail manager based on the current object"""
    class AuditTrailManager(manager.__class__):
        def __init__(self, *arg, **kw):
            super(AuditTrailManager, self).__init__(*arg, **kw)
            self.model = manager.model
    return AuditTrailManager()


def create_audit_model(cls, **kwargs):
    """Create an audit model for the specific class"""
    name = cls.__name__ + 'Audit'

    class Meta:
        db_table = '%s_audit' % cls._meta.db_table
        app_label = cls._meta.app_label
        verbose_name_plural = '%s Audit Trail' % cls._meta.verbose_name
        ordering = ['-_audit_timestamp']

    # Set up a dictionary to simulate declarations within a class
    attrs = {
        '__module__': cls.__module__,
        'Meta': Meta,
        '_audit_timestamp': models.DateTimeField(auto_now_add=True, db_index=True),
        '_audit__str__': cls.__str__.im_func,
        '__str__': lambda self: '%s' % (self._audit__str__()),
        '_audit_track': _track_fields(track_fields=kwargs['track_fields'], unprocessed=True),
    }

    attrs = add_visit_tracking_attrs(cls, attrs)

    attrs = add_sync_attrs(cls, attrs)

    if 'save_change_type' in kwargs and kwargs['save_change_type']:
        attrs['_audit_change_type'] = models.CharField(max_length=1)

    # Copy the fields from the existing model to the edc_audit model
    for field in cls._meta.fields:
        if field.name in attrs:
            raise ImproperlyConfigured(
                "%s cannot use %s as it is needed by AuditTrail." % (cls.__name__, field.attname))
        if isinstance(field, (models.AutoField, UUIDAutoField)):
            # Audit models have a separate AutoField called _audit_id
            # id is demoted to a normal field (or whatever the auto field is named)
            if isinstance(field, UUIDAutoField):
                attrs[field.name] = UUIDField(auto=False, editable=False, primary_key=False)
                new_field = UUIDAutoField(primary_key=True)
            else:
                attrs[field.name] = models.IntegerField(db_index=True, editable=False)
                new_field = models.AutoField(primary_key=True)
            new_field.name = '_audit_{0}'.format(field.name)
            attrs[new_field.name] = new_field
        # begin erikvw added this as OneToOneField was not handled, causes an IntegrityError
        elif isinstance(field, models.OneToOneField):
            rel = copy.copy(field.rel)
            new_field = models.ForeignKey(rel.to, null=field.null)
            new_field.rel.related_name = '_audit_' + field.related_query_name()
            attrs[field.name] = new_field
            # end erikvw added
        else:
            if field.primary_key:
                raise ImproperlyConfigured(
                    "{0}.{1} should not be a primary key! Unhandled by AuditTrail".format(cls, field))
            attrs[field.name] = copy.copy(field)
            # If 'unique' is in there, we need to remove it, otherwise the index
            # is created and multiple edc_audit entries for one item fail.
            attrs[field.name]._unique = False
            # If a model has primary_key = True, a second primary key would be
            # created in the edc_audit model. Set primary_key to false.
            attrs[field.name].primary_key = False
            attrs[field.name].null = field.null
            # Rebuild and replace the 'rel' object to avoid foreign key clashes.
            # Borrowed from the Basie project - please check if adding this is allowed by the license.
            if isinstance(field, models.ForeignKey):
                rel = copy.copy(field.rel)
                rel.related_name = '_audit_' + field.related_query_name()
                attrs[field.name].rel = rel

    for track_field in _track_fields(kwargs['track_fields']):
        if track_field['name'] in attrs:
            raise NameError(
                'Field named "%s" already exists in edc_audit version of %s' % (track_field['name'], cls.__name__))
        attrs[track_field['name']] = copy.copy(track_field['field'])

    return type(name, (models.Model,), attrs)


def add_visit_tracking_attrs(cls, attrs):
    """Adds attrs needed to determine the visit model."""
    try:
        attrs.update({'visit_model': cls.visit_model})
    except AttributeError:
        pass
    try:
        attrs.update({'visit_model_attr': cls.visit_model_attr})
    except AttributeError:
        pass
    return attrs


def add_sync_attrs(cls, attrs):
    try:
        attrs.update({'to_outgoing_transaction': cls.to_outgoing_transaction.im_func})
        attrs.update({'is_serialized': cls.is_serialized.im_func})
        attrs.update({'encrypted_json': cls.encrypted_json.im_func})
        attrs.update({'_deserialize_post': cls._deserialize_post.im_func})
    except AttributeError:
        pass
    try:
        attrs['natural_key'] = cls.natural_key
    except AttributeError:
        pass
    return attrs


def _build_track_field(track_item):
    track = {}
    track['name'] = track_item[0]
    if isinstance(track_item[1], models.Field):
        track['field'] = track_item[1]
    elif issubclass(track_item[1], models.Model):
        track['field'] = models.ForeignKey(track_item[1])
    else:
        raise TypeError('Track fields only support items that are Fields or Models.')
    return track


def _track_fields(track_fields=None, unprocessed=False):
    # Add in the fields from the Audit class "track" attribute.
    track_fields_found = []
#     global_track_fields = getattr(GLOBAL_TRACK_FIELDS, 'GLOBAL_TRACK_FIELDS', [])
    global_track_fields = GLOBAL_TRACK_FIELDS or []
    for track_item in global_track_fields:
        if unprocessed:
            track_fields_found.append(track_item)
        else:
            track_fields_found.append(_build_track_field(track_item))
    if track_fields:
        for track_item in track_fields:
            if unprocessed:
                track_fields_found.append(track_item)
            else:
                track_fields_found.append(_build_track_field(track_item))
    return track_fields_found
