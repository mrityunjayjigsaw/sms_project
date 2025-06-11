from django import forms
from .models import StudentAdmission

class StudentAdmissionForm(forms.ModelForm):
    class Meta:
        model = StudentAdmission
        fields = [
            'admission_no', 'ssr_no', 'full_name', 'gender', 'date_of_birth', 'admission_date',
            'father_name', 'mother_name', 'father_profession',
            'category', 'religion', 'aadhar_no', 'apaar_id',
            'mobile_no', 'whatsapp_no',
            'photo', 'address', 'email'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(StudentAdmissionForm, self).__init__(*args, **kwargs)
        self.fields['admission_no'].widget.attrs['readonly'] = True

    def clean_mobile_no(self):
        mobile = self.cleaned_data['mobile_no']
        if not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError("Mobile number must be exactly 10 digits.")
        return mobile

    def clean_whatsapp_no(self):
        whatsapp = self.cleaned_data.get('whatsapp_no')
        if whatsapp and (not whatsapp.isdigit() or len(whatsapp) != 10):
            raise forms.ValidationError("WhatsApp number must be 10 digits if provided.")
        return whatsapp

    def clean_aadhar_no(self):
        aadhar = self.cleaned_data.get('aadhar_no')
        if aadhar and (not aadhar.isdigit() or len(aadhar) != 12):
            raise forms.ValidationError("Aadhar number must be exactly 12 digits.")
        return aadhar
    
    
from .models import Class, AcademicYear

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'stream', 'is_active']
        

class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
