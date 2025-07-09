from django.db import models
from admission.models import School 
# Create your models here.
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountHead(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    description = models.TextField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE) 

    def __str__(self):
        return f"{self.name} ({self.type})"


 # Assuming each user is linked to a school

class Transaction(models.Model):
    VOUCHER_TYPES = [
    ('payment', 'Payment'),
    ('receipt', 'Receipt'),
    ('journal', 'Journal'),
    ('contra', 'Contra'),
    ]
    date = models.DateField()
    debit_account = models.ForeignKey(AccountHead, on_delete=models.PROTECT, related_name='debit_transactions')
    credit_account = models.ForeignKey(AccountHead, on_delete=models.PROTECT, related_name='credit_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, default="kalawati")  # Multi-school support
    voucher_type = models.CharField(max_length=20, choices=VOUCHER_TYPES, blank=True, null=True)  # ✅ Add this
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=30, editable=False) 


    def __str__(self):
        return f"{self.date} | Dr: {self.debit_account.name} Cr: {self.credit_account.name} ₹{self.amount}"
    
    class Meta:
        unique_together = ('school', 'transaction_id')  # ✅ Enforce per-school uniqueness

# transactions/models.py

class SchoolTransactionCounter(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE)
    last_number = models.PositiveIntegerField(default=0)
