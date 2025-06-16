from django import forms
from django.contrib.auth.models import User
from .models import School

class SchoolSignupForm(forms.ModelForm):
    # User fields (school admin)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = School
        fields = ['name', 'address', 'contact']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
