[![Build Status](https://travis-ci.org/botswana-harvard/edc-audit.svg?branch=develop)](https://travis-ci.org/botswana-harvard/edc-audit)

# edc-audit

(Note: Edc after Django 1.6 uses `simple_history`)

Add an audit trail to your model like this:

	from django.db import models
	
	from edc_audit import AuditTrail
	
	class MyModel(models.Model):
	
		field1 = models.CahrField(max_length=10)
		
		field2 = models.CahrField(max_length=10)
		
		objects = model.Manager()
		
		history = Audittrail()
		
		class Meta:
			app_label = 'my_app"
			
Create an instance of MyModel and review the audit instance created:

	>>> my_model = MyModel.objects.create(field1='pluto', field1='jupiter')
	>>> my_model.history.all()
	[<MyModelAudit: MyModelAudit object>]

## Using with edc.device.sync

`edc_audit` will serialize the history of models that subclass `edc.device.sync.models.BaseSyncUuidModel` or any model that defines a class method `serialize`.

The model would be declared like this

	from django.db import models
	
	from edc_audit import AuditTrail
	
	class MyModel(models.Model):
	
		def serialize(self, *args, **kwargs):
			return my_serializer(*args, **kwargs)

		field1 = models.CharField(max_length=10)
		
		field2 = models.CharField(max_length=10)
		
		objects = model.Manager()
		
		history = Audittrail()
		
		class Meta:
			app_label = 'my_app"
