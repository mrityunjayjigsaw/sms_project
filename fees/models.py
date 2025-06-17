from django.db import models
from transactions.models import AccountHead  # Importing the AccountHead model
from admission.models import StudentAdmission
# Create your models here.
 
class FeeType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # is_recurring = models.BooleanField(default=True, help_text="Checked = monthly recurring")
    account_head = models.ForeignKey(
        AccountHead,
        on_delete=models.PROTECT,
        related_name='fee_types',
        help_text=""
    )

    def __str__(self):
        return self.name


class StudentOpeningBalance(models.Model):
    student = models.OneToOneField(StudentAdmission, on_delete=models.CASCADE)
    opening_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    opening_advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} | Due: ₹{self.opening_due} | Advance: ₹{self.opening_advance}"

class StudentFeePlan(models.Model):
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE, related_name="fee_plans")
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'fee_type')

    def __str__(self):
        return f"{self.student.full_name} - {self.fee_type.name}: ₹{self.amount}"
    

class StudentFeeDue(models.Model):
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    month = models.DateField(help_text="Use 1st of the month for uniformity, e.g. 2025-07-01")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    is_posted = models.BooleanField(default=False)
    carry_forward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'fee_type', 'month')

    def __str__(self):
        return f"{self.student.full_name} | {self.fee_type.name} | ₹{self.amount_due} | {self.month.strftime('%b %Y')}"


class StudentFeePayment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK', 'Online/Bank'),
    ]

    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    month = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='CASH')  # ✅
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.full_name} - ₹{self.total_amount} - {self.month.strftime('%B %Y')}"


class StudentFeePaymentDetail(models.Model):
    payment = models.ForeignKey(StudentFeePayment, on_delete=models.CASCADE, related_name="details")
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.fee_type.name}: ₹{self.amount_paid}"

class StudentAdvanceBalance(models.Model):
    student = models.OneToOneField(StudentAdmission, on_delete=models.CASCADE)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.full_name} - ₹{self.advance_amount} advance"