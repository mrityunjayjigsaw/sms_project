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


class AccountHeadForm(forms.ModelForm):
    class Meta:
        model = AccountHead
        fields = ['name', 'type', 'description', 'opening_balance']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Account Head Name'}),
            'type': forms.Select(),
            'description': forms.Textarea(attrs={'rows': 2}),
            'opening_balance': forms.NumberInput(attrs={'step': '0.01'}),
        }
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        return name.strip().upper() 
    
class AccountHeadBalanceForm(AccountHeadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].disabled = True
        self.fields['type'].disabled = True
