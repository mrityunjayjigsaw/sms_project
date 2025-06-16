from django import forms
from .models import StudentAdmission, StudentAcademicRecord
from .models import Class, AcademicYear

class StudentAdmissionForm(forms.ModelForm):
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=True,
        label="Academic Year"
    )
    class_enrolled = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=True,
        label="Class"
    )
    section = forms.CharField(
        max_length=10,
        required=True,
        label="Section",
        initial='A',# default="A" 
    )
    
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
        mobile_no = self.cleaned_data.get('mobile_no')
        if mobile_no:
            if not str(mobile_no).isdigit():
                raise forms.ValidationError("Mobile number should contain only digits.")
            if len(str(mobile_no)) != 10:
                raise forms.ValidationError("Mobile number must be 10 digits.")
        return mobile_no  # This allows None/empty value to pass

    def clean_whatsapp_no(self):
        whatsapp = self.cleaned_data.get('whatsapp_no')
        if whatsapp:
            whatsapp = str(whatsapp).strip()  # Ensure it's a string and trimmed
            if not whatsapp.isdigit():
                raise forms.ValidationError("WhatsApp number should contain only digits.")
            if len(whatsapp) != 10:
                raise forms.ValidationError("WhatsApp number must be exactly 10 digits.")

        return whatsapp  # Blank values are allowed


    def clean_aadhar_no(self):
        aadhar = self.cleaned_data.get('aadhar_no')
        if aadhar:
            aadhar = str(aadhar).strip()
            if not aadhar.isdigit():
                raise forms.ValidationError("Aadhar number should contain only digits.")
            if len(aadhar) != 12:
                raise forms.ValidationError("Aadhar number must be exactly 12 digits.")
        
        return aadhar  # Blank values are allowed

    


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

class StudentAcademicRecordForm(forms.ModelForm):
    class Meta:
        model = StudentAcademicRecord
        fields = ['academic_year', 'class_enrolled', 'section', 'remarks']
        widgets = {
            'section': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label="Select Excel File (.xlsx)")
