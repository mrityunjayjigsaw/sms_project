# reports/forms.py
from django import forms
from admission.models import StudentAdmission, AcademicYear

class StudentFeeHistoryForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentAdmission.objects.none(), required=True)
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school')
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = StudentAdmission.objects.filter(school=school)
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(school=school)
