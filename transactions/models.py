from django.db import models
from admission.models import School 
# Create your models here.

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

    def __str__(self):
        return f"{self.name} ({self.type})"


 # Assuming each user is linked to a school

class Transaction(models.Model):
    date = models.DateField()
    debit_account = models.ForeignKey(AccountHead, on_delete=models.PROTECT, related_name='debit_transactions')
    credit_account = models.ForeignKey(AccountHead, on_delete=models.PROTECT, related_name='credit_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)  # Multi-school support
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} | Dr: {self.debit_account.name} Cr: {self.credit_account.name} ₹{self.amount}"
