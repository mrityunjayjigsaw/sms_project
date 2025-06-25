from django import forms
from .models import FeeType
from admission.models import *


class FeeTypeForm(forms.ModelForm):
    class Meta:
        model = FeeType
        fields = ['name', 'description', 'account_head']


class BulkFeePlanForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=True)
    class_enrolled = forms.ModelChoiceField(queryset=Class.objects.all(), required=True)
    section = forms.CharField(max_length=10, required=False)



class PostingFeesForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=True)
    class_enrolled = forms.ModelChoiceField(queryset=Class.objects.all(), required=True)
    month = forms.DateField(input_formats=['%Y-%m'], widget=forms.DateInput(attrs={'type': 'month'}), required=True)

# fees/forms.py

class FeeCollectionFilterForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), label="Academic Year")
    class_enrolled = forms.ModelChoiceField(queryset=Class.objects.all(), label="Class")

    month = forms.DateField(
        input_formats=['%Y-%m'],
        widget=forms.DateInput(attrs={'type': 'month'}),
        required=True,
        label="Month (e.g., April 2025)"
    )



class StudentFeeLookupForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=True)
    class_enrolled = forms.ModelChoiceField(queryset=Class.objects.all(), required=True)
    student = forms.ModelChoiceField(queryset=StudentAcademicRecord.objects.none(), required=True, label="Student")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'academic_year' in self.data and 'class_enrolled' in self.data:
            try:
                year_id = int(self.data.get('academic_year'))
                class_id = int(self.data.get('class_enrolled'))
                self.fields['student'].queryset = StudentAcademicRecord.objects.filter(
                    academic_year_id=year_id,
                    class_enrolled_id=class_id
                ).select_related('student')
            except (ValueError, TypeError):
                pass
