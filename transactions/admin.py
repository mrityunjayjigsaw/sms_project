from django.contrib import admin
from .models import Transaction
# Register your models here.
from django.contrib import admin
from .models import AccountHead

@admin.register(AccountHead)
class AccountHeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'opening_balance', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['name']



@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'debit_account', 'credit_account', 'amount', 'school']
    list_filter = ['date', 'debit_account', 'credit_account']
    search_fields = ['remarks']
