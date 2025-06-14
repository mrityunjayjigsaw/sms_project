# transactions/forms.py
from django import forms
from .models import AccountHead, Transaction

class ManualTransactionForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    debit_account = forms.ModelChoiceField(queryset=AccountHead.objects.filter(is_active=True))
    credit_account = forms.ModelChoiceField(queryset=AccountHead.objects.filter(is_active=True))
    amount = forms.DecimalField(min_value=0.01, decimal_places=2)
    voucher_type = forms.ChoiceField(choices=Transaction.VOUCHER_TYPES, required=False)
    remarks = forms.CharField(widget=forms.Textarea, required=False)
