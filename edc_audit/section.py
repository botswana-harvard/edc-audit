# from edc.dashboard.section.classes import BaseSectionView, site_sections
# from edc.core.model_data_inspector.forms import SelectModelForm
# 
# 
# class SectionAuditView(BaseSectionView):
#     section_name = 'audit_trail'
#     section_display_name = 'Audit'
#     section_display_index = 130
#     section_template = 'section_audit_trail.html'
# 
#     def contribute_to_context(self, context, request, *args, **kwargs):
#         context.update({
#             'select_model_form': SelectModelForm().as_p(),
#             'model_name': kwargs.get('model_name')
#             })
#         return context
#
# site_sections.register(SectionAuditView)
