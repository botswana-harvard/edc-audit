[![Build Status](https://travis-ci.org/botswana-harvard/edc-audit.svg?branch=develop)](https://travis-ci.org/botswana-harvard/edc-audit)

# edc-audit

(based on code from Marty Alchin's audit.py)

In the Edc, `AuditTrail` is imported from `edc_base.audit_trail` to simplify changing to `django-simple-history` if and when that happens. 

Add an audit trail to your model like this:

	from django.db import models
	
	from edc_base.audit_trail import AuditTrail
	
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

## Using with `edc_sync`

`edc_audit` generated history models will serialize themselves to model `edc_sync.models.OutgoingTransaction` just like anyother model that uses the `SyncModelMixin` and has `ALLOW_MODEL_SERIALIZATION`=True in `settings.py`. Nothing special needs to be done for this to be implemented. To disable this set `ALLOW_AUDIT_TRAIL_MODEL_SERIALIZATION`=False in `settings.py` (the default is True). If `ALLOW_MODEL_SERIALIZATION`=False then the value of `ALLOW_AUDIT_TRAIL_MODEL_SERIALIZATION` is ignored.


