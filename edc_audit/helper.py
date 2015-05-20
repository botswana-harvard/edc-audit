

def get_subject_identifier(obj):

    """Used by AuditTrail to update an add track field _audit_subject_identifier.

    If the path to the subject identifier is not obvious, add a get_visit() method to
    the model that returns the visit instance:

        def get_visit(self):
            return self.maternal_lab_del_dx.maternal_visit

    """

    subject_identifier = ''

    try:
        if 'get_subject_identifier' in dir(obj):
            subject_identifier = obj.get_subject_identifier()
        elif 'get_visit' in dir(obj):
            subject_identifier = obj.get_visit().appointment.registered_subject.subject_identifier
        elif [fld for fld in obj._meta.fields if fld.name == 'subject_identifier']:
            subject_identifier = obj.subject_identifier
        elif [fld for fld in obj._meta.fields if fld.name == 'subject_visit']:
            subject_identifier = eval('obj.subject_visit.appointment.registered_subject.subject_identifier')
        elif [fld for fld in obj._meta.fields if fld.name == 'appointment']:
            subject_identifier = obj.appointment.registered_subject.subject_identifier
        elif [fld for fld in obj._meta.fields if fld.name == 'registered_subject']:
            subject_identifier = obj.registered_subject.subject_identifier
        else:
            # raise TypeError('AuditTrail cannot find the subject_identifier. Perhaps add a get_visit() or get_subject_identifier() method to the model')
            pass
    except:
        pass
    return subject_identifier
