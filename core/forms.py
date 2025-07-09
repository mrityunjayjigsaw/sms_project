from django import forms
from django.contrib.auth.models import User
from .models import School

class SchoolSignupForm(forms.ModelForm):
    # User fields (school admin)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    # ✅ New field
    short_name = forms.CharField(max_length=10, label="Short School Code (e.g., KWS)", help_text="This will appear in transaction IDs")

    class Meta:
        model = School
        fields = ['name', 'short_name', 'address', 'contact']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_short_name(self):
        short_name = self.cleaned_data['short_name'].upper()
        if School.objects.filter(short_name=short_name).exists():
            raise forms.ValidationError("This short name is already used by another school.")
        return short_name

