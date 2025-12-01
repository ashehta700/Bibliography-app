from django import forms
from django.utils.translation import gettext_lazy as _
# from django.forms import inlineformset_factory
from .models import Report, Type_Report

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            'Library_Reference', 'Date_Issue', 'Type_of_report_ID', 'Title', 'Title_ar',
            'Authors_Name', 'Abstract', 'Abstract_ar', 'Keywords', 'Reference',
            'pdf_file', 'company'
        ]
        labels = {
            'Library_Reference': _("Library Reference"),
            'Date_Issue': _("Year of Issue"),
            'Type_of_report_ID': _("Report Type"),
            'Title': _("Title (EN)"),
            'Title_ar': _("Title (AR)"),
            'Authors_Name': _("Authors"),
            'abstract': _("Abstract (EN)"),
            'Abstract_ar': _("Abstract (AR)"),
            'Keywords': _("Keywords"),
            'Reference': _("References"),
            'pdf_file': _("Upload PDF File"),
            'company': _("Company"),
        }


# class AppendixForm(forms.ModelForm):
#     class Meta:
#         model = Appendix_table
#         fields = ['Name_of_appendix', 'pdf_file', 'Notes', 'Type_of_report_ID']
#         widgets = {
#             'Name_of_appendix': forms.TextInput(attrs={'class': 'form-control'}),
#             'pdf_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
#             'Notes': forms.TextInput(attrs={'class': 'form-control'}),
#             'Type_of_report_ID': forms.Select(attrs={'class': 'form-select'}),
#         }
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if self.instance and self.instance.pk:
#             self.fields['pdf_file'].required = False


# Define default AppendixFormSet with no extra forms (you can override in views)
# AppendixFormSet = inlineformset_factory(
#     Report,
#     Appendix_table,
#     form=AppendixForm,
#     extra=0,
#     can_delete=True,
# )
