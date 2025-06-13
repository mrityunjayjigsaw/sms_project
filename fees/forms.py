from django import forms
from .models import FeeType
from admission.models import AcademicYear, Class

class FeeTypeForm(forms.ModelForm):
    class Meta:
        model = FeeType
        fields = ['name', 'description', 'is_recurring', 'account_head']


class BulkFeePlanForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=True)
    class_enrolled = forms.ModelChoiceField(queryset=Class.objects.all(), required=True)
    section = forms.CharField(max_length=10, required=False)



class PostingFeesForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=True)
    class_enrolled = forms.ModelChoiceField(queryset=Class.objects.all(), required=True)
    month = forms.DateField(input_formats=['%Y-%m'], widget=forms.DateInput(attrs={'type': 'month'}), required=True)
