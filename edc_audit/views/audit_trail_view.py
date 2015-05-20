from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.shortcuts import render_to_response
from django.template import RequestContext

from edc_base.model.models import BaseModel
from edc.core.model_selector.classes import ModelSelector
from edc.dashboard.section.classes import section_index_view

from ..forms import AuditTrailForm
from ..models import AuditComment


@login_required
def audit_trail_view(request, **kwargs):

    """ Using app_label and model_name present the cls+'_audit' table"""

    options = kwargs or {}
    for k, v in request.GET.iteritems():
        options.update({k: v})
    section_name = kwargs.get('section_name')

    audit_subject_identifier = request.GET.get('audit_subject_identifier', kwargs.get('audit_subject_identifier'))
    if audit_subject_identifier:
        audit_comments = AuditComment.objects.filter(audit_subject_identifier=audit_subject_identifier)
    else:
        audit_comments = AuditComment.objects.none()
    dashboard_type = request.GET.get('dashboard_type', kwargs.get('dashboard_type'))
    back_url_name = request.GET.get('back_url_name', kwargs.get('back_url_name'))

    field_labels = []
    field_names = []
    display_rows = []
    model = None
    history = None
    report_title = 'Audit Trail'
    app_label = ''
    model_name = ''
    verbose_name = ''
    template = 'section_audit_trail.html'
    err_message = ''
    status_message = ''

    if request.method == 'POST':

        # form to select the app and model
        form = AuditTrailForm(request.POST)

        if form.is_valid():
            app_label = form.cleaned_data['app_label']
            model_name = form.cleaned_data['model_name']
            audit_subject_identifier = form.cleaned_data['audit_subject_identifier']
            dashboard_type = form.cleaned_data['dashboard_type']
            visit_code = form.cleaned_data['visit_code']
            visit_instance = form.cleaned_data['visit_instance']
            back_url_name = form.cleaned_data['back_url_name']

            model_selector = ModelSelector(app_label, model_name)

            if app_label and model_name:
                try:
                    # try to get the model and access the history manager, or fail.
                    model = apps.get_model(app_label, model_name)
                    history = model.history.all().order_by('_audit_id')
                    verbose_name = model._meta.verbose_name
                    report_title = 'Audit Trail for {app_label}.{model_name}'.format(app_label=app_label, model_name=model._meta.verbose_name)
                except:
                    err_message = 'Cannot find model {app_label}.{model_name}.'.format(app_label=app_label, model_name=model_name)

            if history:
                # for the template, prepare separate ordered lists of field labels and field names
                field_labels = [
                    'audit_id', 'type', 'time', 'user'] + [
                    fld.name for fld in history[0]._meta.fields if fld.column[-3:] == '_id' and fld.name != '_audit_id'] + [
                    fld.name for fld in history[0]._meta.fields if fld not in BaseModel._meta.fields and fld.name != 'id' and fld.column[0] != '_' and fld.column[-3:] != '_id'] + [
                    fld.name for fld in BaseModel._meta.fields if fld.name != 'user_modified'
                ]

                # for now, manually remove rando field rx, develop a better mechanism later...
                try:
                    field_labels.remove('rx')
                except:
                    pass

                field_labels = [' '.join(name.split('_')) for name in field_labels]

                field_names = [
                    '_audit_id', '_audit_change_type', '_audit_timestamp', 'user_modified'] + [
                    fld.name for fld in history[0]._meta.fields if fld.column[-3:] == '_id' and fld.name != '_audit_id'] + [
                    fld.name for fld in history[0]._meta.fields if fld not in BaseModel._meta.fields and fld.name != 'id' and fld.column[0] != '_' and fld.column[-3:] != '_id'] + [
                    fld.name for fld in BaseModel._meta.fields if fld.name != 'user_modified'
                ]
                try:
                    field_names.remove('rx')
                except:
                    pass

                # store values in a ordered list
                display_rows = []

                if audit_subject_identifier:
                    try:
                        history_rows = model.history.filter(_audit_subject_identifier__icontains=audit_subject_identifier).order_by('_audit_timestamp')
                    except:
                        raise AttributeError('Audit field _audit_subject_identifier is required by edc_audit trail view. '
                                             'does not exists. Did you create settings_audit.y and set \'GLOBAL_TRACK_FIELDS\'?')
                else:
                    history_rows = model.history.all().order_by('_audit_timestamp')

                for row in history_rows:
                    this_row = []
                    # append a comment pk (send comment as first item for convenience of template)
                    if AuditComment.objects.filter(app_label=app_label, model_name=model_name, audit_id=row.pk, audit_subject_identifier=row._audit_subject_identifier):
                        this_row.append(AuditComment.objects.get(app_label=app_label, model_name=model_name, audit_id=row.pk, audit_subject_identifier=row._audit_subject_identifier).pk)
                    else:
                        this_row.append('add')
                    for field_name in field_names:
                        if not field_name == 'rx':
                            try:
                                # try if the field has a choices tuple, use get_FOO_display(), or fail
                                this_row.append(eval('row.get_' + field_name + '_display()'))
                            except:
                                this_row.append(getattr(row, field_name))

                    display_rows.append(this_row)
                if not display_rows:
                    if audit_subject_identifier:
                        status_message = 'There are no entries in the edc_audit trail of this model for %s.' % (audit_subject_identifier,)
                    else:
                        status_message = 'There are no entries in the edc_audit trail for this model.'

            else:
                status_message = 'There are no entries in the edc_audit trail for this model.'
    else:
        app_label = request.GET.get('app_label', kwargs.get('app_label'))
        model_name = request.GET.get('dashboard_model', kwargs.get('dashboard_model'))
        audit_subject_identifier = request.GET.get('audit_subject_identifier', kwargs.get('audit_subject_identifier'))

        form = AuditTrailForm()
        form.fields['app_label'].initial = app_label
        form.fields['model_name'].initial = model_name
        form.fields['audit_subject_identifier'].initial = audit_subject_identifier

        model_selector = ModelSelector(app_label, model_name)
        # these parameters are ugly, they couple to bhp_dashboard! Same in form and template
        dashboard_type = request.GET.get('dashboard_type', kwargs.get('dashboard_type'))
        visit_code = request.GET.get('visit_code', kwargs.get('visit_code'))
        visit_instance = request.GET.get('visit_instance', kwargs.get('visit_instance'))
        back_url_name = request.GET.get('back_url_name', kwargs.get('back_url_name'))
        if not back_url_name and options.get('visit_code', None) and options.get('visit_instance', None):
            back_url_name = 'dashboard_visit_url'
    options.update({
        'sections': section_index_view.get_section_name_list(),
        'selected_section': section_name,
        'section_name': section_name,
        'report_title': report_title,
        'verbose_name': verbose_name,
        'history': history,
        'field_labels': field_labels,
        'field_names': field_names,
        'display_rows': display_rows,
        'form': form,
        'err_message': err_message,
        'status_message': status_message,
        'app_label': app_label,
        'model_name': model_name,
        'audit_subject_identifier': audit_subject_identifier,
        'audit_comments': audit_comments,
        'dashboard_type': dashboard_type,
        'visit_code': visit_code,
        'visit_instance': visit_instance,
        'back_url_name': back_url_name,
        'app_labels': model_selector.get_app_labels(),
        'model_names': model_selector.get_model_names(),
    })
    return render_to_response(template, options, context_instance=RequestContext(request))
