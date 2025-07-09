from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import *
import os
from django.shortcuts import render, redirect,get_object_or_404
from .forms import *
from admission.models import *
from transactions.models import *
from django.db import transaction
from django.db.models import Q, Sum
from datetime import datetime,date, timedelta
from decimal import Decimal


def fees_home(request):
    return render(request, 'fees/fees_home.html')


def add_fee_type(request):
    form = FeeTypeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('fee_type_list')  # Create this view or replace with your dashboard

    return render(request, 'fees/add_fee_type.html', {'form': form})


def fee_type_list(request):
    fee_types = FeeType.objects.all()
    return render(request, 'fees/fee_type_list.html', {'fee_types': fee_types})


def assign_fee_plan_bulk(request):
    form = BulkFeePlanForm(request.POST or None)
    students = []
    fee_types = FeeType.objects.all()

    if request.method == 'POST' and 'filter_students' in request.POST:
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            class_enrolled = form.cleaned_data['class_enrolled']
            section = form.cleaned_data.get('section')

            students = StudentAcademicRecord.objects.filter(
                academic_year=academic_year,
                class_enrolled=class_enrolled,
                section=section,
                school=request.user.userprofile.school
            ).select_related('student')

    if request.method == 'POST' and 'save_fee_plan' in request.POST:
        fee_types = FeeType.objects.all()
        for key, value in request.POST.items():
            if key.startswith("amount_"):
                _, student_id, fee_type_id = key.split("_")
                amount = value.strip()
                if amount:
                    StudentFeePlan.objects.update_or_create(
                        student_id=student_id,
                        fee_type_id=fee_type_id,
                        defaults={'amount': amount}
                    )
        return redirect('fees_home')

    return render(request, 'fees/assign_fee_plan_bulk.html', {
        'form': form,
        'students': students,
        'fee_types': fee_types,
    })


def assign_fees_bulk(request):
    form = PostingFeesForm(request.POST or None)
    students = []
    fee_types = FeeType.objects.all()
    already_posted = False  # always define early
    selected_month = None
    selected_year_id = None
    selected_class_id = None

    if request.method == 'POST' and 'filter_students' in request.POST:
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            class_enrolled = form.cleaned_data['class_enrolled']
            month = form.cleaned_data['month']
            school = request.user.userprofile.school

            selected_month = month
            selected_year_id = academic_year.id
            selected_class_id = class_enrolled.id

            # Fetch students in selected class & year
            students = StudentAcademicRecord.objects.filter(
                academic_year=academic_year,
                class_enrolled=class_enrolled,
                school=school
            ).select_related('student')

            # Get 1st of previous month
            first_day_of_month = month.replace(day=1)
            previous_month = first_day_of_month - timedelta(days=1)
            prev_month_start = previous_month.replace(day=1)

            # Fill student.previous_fee_keys from previous dues or fee plan
            for record in students:
                student = record.student
                student.previous_fee_keys = {}

                for fee_type in fee_types:
                    try:
                        if month.month == 4:
                            # For April, there is no previous month, so use April itself if exists
                            due = StudentFeeDue.objects.get(
                                student=student,
                                fee_type=fee_type,
                                month=month,
                                is_posted=True
                            )
                        else:
                            # For other months, fetch from previous month
                            due = StudentFeeDue.objects.get(
                                student=student,
                                fee_type=fee_type,
                                month=prev_month_start,
                                is_posted=True
                            )
                        amount = due.original_due
                    except StudentFeeDue.DoesNotExist:
                        try:
                            plan = StudentFeePlan.objects.get(student=student, fee_type=fee_type)
                            amount = plan.amount
                        except StudentFeePlan.DoesNotExist:
                            amount = ""

                    student.previous_fee_keys[fee_type.id] = amount
            
            # Check if any fee already posted for selected month
            student_ids = [record.student.id for record in students]
            posted_dues = StudentFeeDue.objects.filter(
                student_id__in=student_ids,
                month=month,
                is_posted=True
            )
            already_posted = posted_dues.exists()

    elif request.method == 'POST' and 'post_fees' in request.POST:
        with transaction.atomic():
            month_str = request.POST.get('month')  # e.g. "2025-04"
            try:
                month_date = date.fromisoformat(month_str + "-01")
            except (TypeError, ValueError):
                month_date = date.today().replace(day=1)

            student_ids = request.POST.getlist('student_ids')
            for student_id in student_ids:
                student_id = int(student_id)
                student = StudentAcademicRecord.objects.get(student__id=student_id).student

                for fee_type in fee_types:
                    field_key = f"amount_{student_id}_{fee_type.id}"
                    amount = request.POST.get(field_key)

                    if amount:
                        amount = float(amount)

                        # Save fee due
                        due, created = StudentFeeDue.objects.update_or_create(
                            student=student,
                            fee_type=fee_type,
                            month=month_date,
                            defaults={'original_due':amount,
                                      'amount_due': amount, 
                                      'is_posted': True}
                        )

                        # Create accounting transaction
                        Transaction.objects.create(
                            date=month_date,
                            debit_account=AccountHead.objects.get(name="STUDENT_DUES"),
                            credit_account=fee_type.account_head,
                            amount=amount,
                            remarks=f"Posted fee for {student.full_name} - {fee_type.name} - {month_date.strftime('%B %Y')}",
                            school=student.school,
                            voucher_type='journal',
                            created_by=request.user,
                            created_at=datetime.now()    
                        )
        return redirect('fees_home')

    return render(request, 'fees/assign_fees_bulk.html', {
        'form': form,
        'students': students,
        'fee_types': fee_types,
        'selected_month': selected_month,
        'selected_year_id': selected_year_id,
        'selected_class_id': selected_class_id,
        'already_posted': already_posted,
    })


def view_remaining_due_detail(request):
    form = PostingFeesForm(request.POST or None)
    students = []
    fee_types = FeeType.objects.all()
    dues_dict = {}

    if request.method == 'POST' and form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        class_enrolled = form.cleaned_data['class_enrolled']
        month = form.cleaned_data['month']
        school = request.user.userprofile.school

        # Get students in class/year
        students = StudentAcademicRecord.objects.filter(
            academic_year=academic_year,
            class_enrolled=class_enrolled,
            school=school
        ).select_related('student')

        # Fetch dues for selected month
        for record in students:
            student = record.student
            student.due_map = {} #A new attribute due_map is added to each student object to store a mapping of fee_type.id → amount_due.

            for fee_type in fee_types:
                due = StudentFeeDue.objects.filter(
                    student=student,
                    fee_type=fee_type,
                    month=month,
                    is_posted=True
                ).first()
                student.due_map[fee_type.id] = due.amount_due if due else ""

    return render(request, 'fees/view_remaining_due_detail.html', {
        'form': form,
        'students': students,
        'fee_types': fee_types,
    })

from datetime import date 
# Define your months manually
MONTH_CHOICES = [
    'April', 'May', 'June', 'July', 'August', 'September',
    'October', 'November', 'December', 'January', 'February', 'March'
]

MONTH_NAME_TO_NUMBER = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12
}

def view_remaining_due_by_student(request):
    form = StudentFeeLookupForm(request.POST or None)
    student = None
    fee_types = FeeType.objects.all()
    fee_data = {}
    total_per_month = {}
    total_per_fee_type = {}
    grand_total = 0

    if request.method == 'POST' and form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        class_enrolled = form.cleaned_data['class_enrolled']
        school = request.user.userprofile.school

        # Get the StudentAcademicRecord selected
        record = form.cleaned_data['student']

        # Ensure record belongs to selected school, year, and class
        if (record.academic_year == academic_year and 
            record.class_enrolled == class_enrolled and 
            record.school == school):

            student = record.student
            start_year = academic_year.start_date.year
            end_year = academic_year.end_date.year

            for month_name in MONTH_CHOICES:
                fee_data[month_name] = {}
                month_number = MONTH_NAME_TO_NUMBER[month_name]

                year = start_year if month_number >= 4 else end_year
                month_date = date(year, month_number, 1)

                row_total = 0

                for fee_type in fee_types:
                    due = StudentFeeDue.objects.filter(
                        student=student,
                        fee_type=fee_type,
                        month=month_date,
                        is_posted=True
                    ).first()

                    amount = float(due.amount_due) if due else 0
                    fee_data[month_name][fee_type.name] = amount if amount else ""

                    if amount:
                        row_total += amount
                        total_per_fee_type[fee_type.name] = total_per_fee_type.get(fee_type.name, 0) + amount

                total_per_month[month_name] = row_total
                grand_total += row_total

    return render(request, 'fees/view_remaining_due_by_student.html', {
        'form': form,
        'student': student,
        'fee_data': fee_data,
        'fee_types': fee_types,
        'months': MONTH_CHOICES,
        'total_per_month': total_per_month,
        'total_per_fee_type': total_per_fee_type,
        'grand_total': grand_total,
    })

def view_posted_fees(request):
    form = PostingFeesForm(request.POST or None)
    students = []
    fee_types = FeeType.objects.all()

    if request.method == 'POST' and form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        class_enrolled = form.cleaned_data['class_enrolled']
        month = form.cleaned_data['month']
        school = request.user.userprofile.school

        students = StudentAcademicRecord.objects.filter(
            academic_year=academic_year,
            class_enrolled=class_enrolled,
            school=school
        ).select_related('student')

        for record in students:
            student = record.student
            student.posted_map = {}

            for fee_type in fee_types:
                due = StudentFeeDue.objects.filter(
                    student=student,
                    fee_type=fee_type,
                    month=month,
                    is_posted=True
                ).first()
                student.posted_map[fee_type.id] = due.original_due if due else ""

    return render(request, 'fees/view_posted_fees.html', {
        'form': form,
        'students': students,
        'fee_types': fee_types,
    })

def view_posted_fees_by_student(request):
    form = StudentFeeLookupForm(request.POST or None)
    student = None
    fee_types = FeeType.objects.all()
    fee_data = {}
    total_per_month = {}
    total_per_fee_type = {}
    grand_total = 0

    if request.method == 'POST' and form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        class_enrolled = form.cleaned_data['class_enrolled']
        school = request.user.userprofile.school
        record = form.cleaned_data['student']

        if (record.academic_year == academic_year and 
            record.class_enrolled == class_enrolled and 
            record.school == school):

            student = record.student
            start_year = academic_year.start_date.year
            end_year = academic_year.end_date.year

            for month_name in MONTH_CHOICES:
                fee_data[month_name] = {}
                month_number = MONTH_NAME_TO_NUMBER[month_name]
                year = start_year if month_number >= 4 else end_year
                month_date = date(year, month_number, 1)

                row_total = 0

                for fee_type in fee_types:
                    due = StudentFeeDue.objects.filter(
                        student=student,
                        fee_type=fee_type,
                        month=month_date,
                        is_posted=True
                    ).first()

                    amount = float(due.original_due) if due else 0
                    fee_data[month_name][fee_type.name] = amount if amount else ""

                    if amount:
                        row_total += amount
                        total_per_fee_type[fee_type.name] = total_per_fee_type.get(fee_type.name, 0) + amount

                total_per_month[month_name] = row_total
                grand_total += row_total

    return render(request, 'fees/view_posted_fees_by_student.html', {
        'form': form,
        'student': student,
        'fee_data': fee_data,
        'fee_types': fee_types,
        'months': MONTH_CHOICES,
        'total_per_month': total_per_month,
        'total_per_fee_type': total_per_fee_type,
        'grand_total': grand_total,
    })


def fee_collection_filter(request):
    form = FeeCollectionFilterForm(request.POST or None)
    students = []
    selected_payment_date_str = None

    if request.method == 'POST' and form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        class_enrolled = form.cleaned_data['class_enrolled']
        payment_date = form.cleaned_data['payment_date']
        school = request.user.userprofile.school

        selected_payment_date_str = payment_date.strftime('%Y-%m-%d')

        students = StudentAcademicRecord.objects.filter(
            academic_year=academic_year,
            class_enrolled=class_enrolled,
            school=school
        ).select_related('student')

    return render(request, 'fees/fee_collection_filter.html', {
        'form': form,
        'students': students,
        'selected_payment_date': selected_payment_date_str
    })


def collect_fee_step2(request, student_id, payment_date):
    student = get_object_or_404(StudentAdmission, id=student_id)
    payment_date_obj = date.fromisoformat(payment_date)
    fee_types = FeeType.objects.all()
    dues = StudentFeeDue.objects.filter(student=student, is_posted=True).order_by('month')
    advance_obj, _ = StudentAdvanceBalance.objects.get_or_create(student=student)
#     ✅ Tries to get an existing StudentAdvanceBalance object for the given student.
#     ❌ If it doesn't exist, it creates a new one with default values.
    advance_amount = advance_obj.advance_amount
    total_due = dues.aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')
    
#       This is a Django ORM aggregate query, which means:
#       It computes a single value, not a queryset.
#       In this case, it returns a dictionary like: {'total': <sum of all amount_due fields in dues>}


    if request.method == 'POST' and 'allocate' in request.POST:
        amount_paid = Decimal(request.POST.get('amount_paid', '0')) # Default to 0 if not specified
        payment_mode = request.POST.get('payment_mode', 'CASH') # Default to CASH if not specified
        remaining = amount_paid + advance_amount # Total amount available for allocation
        allocated = []  # List to store allocated amounts for each due

        for due in dues:# Iterate through each due
            if remaining <= 0:# If no remaining amount, break the loop
                break
            alloc = min(remaining, due.amount_due)# Allocate the minimum of remaining amount or due amount
            if alloc > 0:# If allocation is greater than 0, update the due
                allocated.append({
                    'month': due.month,
                    'fee_type': due.fee_type,
                    'amount': alloc
                })# Append the allocation to the list
            remaining -= Decimal(alloc)# Update remaining amount after allocation

        return render(request, 'fees/collect_fee_step2.html', {
            'student': student,
            'payment_date': payment_date_obj,
            'dues': dues,
            'advance': advance_amount,
            'amount_paid': amount_paid,
            'allocated': allocated,
            'payment_mode': payment_mode,
            'step': 'preview',
            'total_due': total_due,
        })

    if request.method == 'POST' and 'submit_payment' in request.POST:
        amount_paid = Decimal(request.POST.get('amount_paid', '0'))
        payment_mode = request.POST.get('payment_mode', 'CASH')
        remaining = amount_paid + advance_amount

        with transaction.atomic():
            total_allocated = Decimal('0.00')
            payment = StudentFeePayment.objects.create(
                student=student,
                payment_date=payment_date_obj,
                total_amount=amount_paid,
                payment_mode=payment_mode,
                remarks=f"Fees collected for {payment_date_obj.strftime('%B %Y')}"
            )
# StudentFeePayment holds the amount paid, payment date, mode, and remarks.
# StudentFeePaymentDetail holds the details of each fee type paid and in this amount is equal to allocated amount not the original paid amount.
            for due in dues:
                if remaining <= 0:
                    break
                alloc = min(remaining, due.amount_due)
                if alloc > 0:
                    due.amount_due -= Decimal(alloc)
                    due.save()

                    StudentFeePaymentDetail.objects.create(
                        payment=payment,
                        fee_type=due.fee_type,
                        amount_paid=Decimal(alloc)
                    )

                    Transaction.objects.create(
                        date=payment_date_obj,
                        debit_account=AccountHead.objects.get(name="CASH" if payment_mode == "CASH" else "BANK"),
                        credit_account=AccountHead.objects.get(name="STUDENT_DUES"),
                        amount=Decimal(alloc),
                        remarks=f"{student.full_name} - {due.fee_type.name} ({due.month.strftime('%B %Y')})",
                        school=student.school,
                        voucher_type='receipt',
                        created_by=request.user,
                        created_at=datetime.now()
                    )

                    total_allocated += Decimal(alloc)

                remaining -= Decimal(alloc)

            advance_obj.advance_amount = remaining# This updates the advance amount after allocation
            advance_obj.save()

        return render(request, 'fees/collection_success.html', {
            'student': student,
            'amount_paid': amount_paid,
            'allocated': total_allocated,
            'carry_forward': remaining,
            'payment_mode': payment_mode,
            'payment': payment,
        })

    return render(request, 'fees/collect_fee_step2.html', {
        'student': student,
        'payment_date': payment_date_obj,
        'dues': dues,
        'advance': advance_amount,
        'step': 'entry',
        'total_due': total_due,
    })



from django.db.models import Q

def download_receipt(request, payment_id):
    payment = StudentFeePayment.objects.select_related('student').prefetch_related('details__fee_type').get(id=payment_id)

    # Rebuild detailed data with due info
    full_details = []
    for detail in payment.details.all():
        # Try to find the matching due for this fee type and student
        due = StudentFeeDue.objects.filter(
            student=payment.student,
            fee_type=detail.fee_type,
            is_posted=True,
            month__lte=payment.payment_date  # Optional: Filter only dues before payment date
        ).order_by('-month').first()  # Use latest posted month if multiple found

        full_details.append({
            'fee_type': detail.fee_type.name,
            'amount_paid': detail.amount_paid,
            'original_due': due.original_due if due else '',
            'due_month': due.month.strftime('%B %Y') if due else '',
        })

    template_path = 'fees/fee_receipt.html'
    context = {
        'payment': payment,
        'student': payment.student,
        'details': full_details,
        'school_name': 'My School Name',
        'logo_url': os.path.join('static', 'school_logo.png'),
        'copy_types': ['Student', 'Office'],
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="receipt_{payment.student.full_name}_{payment.payment_date.strftime("%Y_%m")}.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had errors rendering PDF', status=500)
    return response




def classwise_total_dues(request):
    selected_class = None
    selected_year = None
    students_data = []

    if request.method == 'POST':
        selected_class_id = request.POST.get('class_id')
        selected_year_id = request.POST.get('year_id')

        if selected_class_id and selected_year_id:
            selected_class = Class.objects.get(id=selected_class_id)
            selected_year = AcademicYear.objects.get(id=selected_year_id)

            academic_records = StudentAcademicRecord.objects.filter(
                class_enrolled=selected_class,
                academic_year=selected_year,
                student__is_active=True
            ).select_related('student')

            for record in academic_records:
                student = record.student

                # 1. Total fees posted (all time)
                total_original_due = StudentFeeDue.objects.filter(
                    student=student
                ).aggregate(total=Sum('original_due'))['total'] or 0

                # 2. Total payments received (all time)
                total_paid = StudentFeePaymentDetail.objects.filter(
                    payment__student=student
                ).aggregate(total=Sum('amount_paid'))['total'] or 0

                # 3. Advance balance (from model)
                try:
                    advance_balance = StudentAdvanceBalance.objects.get(student=student).advance_amount
                except StudentAdvanceBalance.DoesNotExist:
                    advance_balance = 0

                # 4. Net due = posted - paid - advance
                net_due = total_original_due - total_paid - advance_balance

                if net_due < 0:
                    status = f"Advance ₹{abs(net_due)}"
                    net_due = 0
                elif net_due == 0:
                    status = "No Dues"
                else:
                    status = f"Due ₹{net_due}"

                students_data.append({
                    'student': student,
                    'father_name': student.father_name,
                    'section': record.section,
                    'total_due': net_due,
                    'status': status,
                })

    context = {
        'classes': Class.objects.all(),
        'years': AcademicYear.objects.all(),
        'selected_class': selected_class,
        'selected_year': selected_year,
        'students_data': students_data,
    }

    return render(request, 'fees/classwise_total_dues.html', context)


# views.py

from django.shortcuts import render
from admission.models import Class, AcademicYear, StudentAcademicRecord
from django.utils.timezone import now

def list_students_for_ledger(request):
    selected_class = None
    selected_year = None
    students_data = []

    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        year_id = request.POST.get('year_id')

        if class_id and year_id:
            selected_class = Class.objects.get(id=class_id)
            selected_year = AcademicYear.objects.get(id=year_id)

            records = StudentAcademicRecord.objects.filter(
                class_enrolled=selected_class,
                academic_year=selected_year,
                student__is_active=True
            ).select_related('student')

            for record in records:
                students_data.append({
                    'student': record.student,
                    'section': record.section,
                    'father_name': record.student.father_name,
                    'record_id': record.id
                })

    context = {
        'classes': Class.objects.all(),
        'years': AcademicYear.objects.all(),
        'selected_class': selected_class,
        'selected_year': selected_year,
        'students_data': students_data,
        'today': now().date()
    }
    return render(request, 'fees/student_list_for_ledger.html', context)

from django.shortcuts import render, get_object_or_404
from django.utils.dateparse import parse_date
from datetime import date
from decimal import Decimal
from operator import itemgetter

from .models import StudentAdmission, StudentFeeDue, StudentFeePayment

def student_ledger(request, student_id):
    student = get_object_or_404(StudentAdmission, id=student_id)

    # Parse date range from GET or use defaults
    from_date = parse_date(request.GET.get('from_date')) or date(2024, 1, 1)
    to_date = parse_date(request.GET.get('to_date')) or date.today()

    # 1. Get dues posted within the date range
    dues = StudentFeeDue.objects.filter(
        student=student,
        month__gte=from_date,
        month__lte=to_date
    ).order_by('month')

    # 2. Get actual payments (total paid by student, not just allocated)
    payments = StudentFeePayment.objects.filter(
        student=student,
        payment_date__gte=from_date,
        payment_date__lte=to_date
    ).order_by('payment_date')

    # 3. Prepare ledger entries (both dues and payments)
    ledger_entries = []

    for due in dues:
        ledger_entries.append({
            'date': due.month,
            'type': 'Fee Posted',
            'description': f"{due.fee_type.name} Fee Posted",
            'amount': due.original_due,
            'direction': 'debit'
        })

    for pay in payments:
        ledger_entries.append({
            'date': pay.payment_date,
            'type': 'Payment Received',
            'description': f"Payment Received ({pay.payment_mode})",
            'amount': pay.total_amount,
            'direction': 'credit'
        })

    # 4. Sort entries by date
    ledger_entries.sort(key=itemgetter('date'))

    # 5. Compute running balance and detect advance
    balance = Decimal('0.00')
    for entry in ledger_entries:
        if entry['direction'] == 'debit':
            balance += Decimal(entry['amount'])
        else:
            balance -= Decimal(entry['amount'])

        entry['balance'] = balance

        # Show advance line if balance becomes negative
        if entry['balance'] < 0:
            entry['advance_note'] = f"Advance ₹{abs(entry['balance'])}"
        else:
            entry['advance_note'] = ""

    context = {
        'student': student,
        'ledger_entries': ledger_entries,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, 'fees/student_ledger.html', context)
# This view handles the student ledger, showing all dues and payments in a single timeline.











