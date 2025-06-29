from django.contrib import admin
from .models import StudentOpeningBalance, StudentFeePlan, FeeType, StudentFeeDue
from .models import StudentFeePayment, StudentFeePaymentDetail
from .models import StudentAdvanceBalance
# Register your models here.

@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_head']
    search_fields = ['name']



@admin.register(StudentOpeningBalance)
class StudentOpeningBalanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'opening_due', 'opening_advance', 'created_at']
    search_fields = ['student__full_name']


@admin.register(StudentFeePlan)
class StudentFeePlanAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_type', 'amount', 'is_active']
    list_filter = ['fee_type', 'is_active']
    search_fields = ['student__full_name']
    


@admin.register(StudentFeeDue)
class StudentFeeDueAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_type', 'month', 'amount_due', 'is_posted']
    list_filter = ['month', 'fee_type', 'is_posted']
    search_fields = ['student__full_name']


class PaymentDetailInline(admin.TabularInline):
    model = StudentFeePaymentDetail
    extra = 0

@admin.register(StudentFeePayment)
class StudentFeePaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'payment_date', 'total_amount', 'date']
    inlines = [PaymentDetailInline]



@admin.register(StudentAdvanceBalance)
class StudentAdvanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'advance_amount', 'updated_at']
