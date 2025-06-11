from django import forms
from .models import StudentAdmission

class StudentAdmissionForm(forms.ModelForm):
    class Meta:
        model = StudentAdmission
        fields = [
            'ssr_no', 'full_name', 'gender', 'date_of_birth', 'photo',
            'parent_name', 'address', 'contact_number', 'email'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
