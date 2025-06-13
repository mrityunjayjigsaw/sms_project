
from django.shortcuts import render, redirect,get_object_or_404
from .forms import *
from admission.models import *
from .models import *
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
                        prev_due = StudentFeeDue.objects.get(
                            student=student,
                            fee_type=fee_type,
                            month=prev_month_start
                        )
                        amount = prev_due.amount_due
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
                            defaults={'amount_due': amount, 'is_posted': True}
                        )

                        # Create accounting transaction
                        Transaction.objects.create(
                            date=month_date,
                            debit_account=AccountHead.objects.get(name="STUDENT_DUES"),
                            credit_account=fee_type.account_head,
                            amount=amount,
                            remarks=f"Posted fee for {student.full_name} - {fee_type.name} - {month_date.strftime('%B %Y')}",
                            school=student.school
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


def view_posted_fees_detail(request):
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
            student.due_map = {}

            for fee_type in fee_types:
                due = StudentFeeDue.objects.filter(
                    student=student,
                    fee_type=fee_type,
                    month=month,
                    is_posted=True
                ).first()
                student.due_map[fee_type.id] = due.amount_due if due else ""

    return render(request, 'fees/view_posted_fees_detail.html', {
        'form': form,
        'students': students,
        'fee_types': fee_types,
    })

# fees/views.py


def fee_collection_filter(request):
    form = FeeCollectionFilterForm(request.POST or None)
    students = []
    selected_month_str = None

    if request.method == 'POST' and form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        class_enrolled = form.cleaned_data['class_enrolled']
        month = form.cleaned_data['month']  # this will be a `date` object like 2025-04-01
        school = request.user.userprofile.school

        selected_month_str = month.strftime('%Y-%m')  # for URL in student list

        students = StudentAcademicRecord.objects.filter(
            academic_year=academic_year,
            class_enrolled=class_enrolled,
            school=school
        ).select_related('student')

    return render(request, 'fees/fee_collection_filter.html', {
        'form': form,
        'students': students,
        'selected_month': selected_month_str
    })


def collect_fee_step2(request, student_id, month_str):
    student = get_object_or_404(StudentAdmission, id=student_id)
    month_date = date.fromisoformat(month_str + "-01")
    fee_types = FeeType.objects.all()
    dues = StudentFeeDue.objects.filter(student=student, is_posted=True).order_by('month')
    advance_obj, _ = StudentAdvanceBalance.objects.get_or_create(student=student)
    advance_amount = advance_obj.advance_amount
    total_due = dues.aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')

    if request.method == 'POST' and 'allocate' in request.POST:
        amount_paid = Decimal(request.POST.get('amount_paid', '0'))
        payment_mode = request.POST.get('payment_mode', 'CASH')
        remaining = amount_paid + advance_amount
        allocated = []

        for due in dues:
            if remaining <= 0:
                break
            alloc = min(remaining, due.amount_due)
            if alloc > 0:
                allocated.append({
                    'month': due.month,
                    'fee_type': due.fee_type,
                    'amount': alloc
                })
            remaining -= Decimal(alloc)

        return render(request, 'fees/collect_fee_step2.html', {
            'student': student,
            'month': month_date,
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
                month=month_date,
                total_amount=amount_paid,
                payment_mode=payment_mode,
                remarks=f"Fees collected for {month_date.strftime('%B %Y')}"
            )

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
                        date=date.today(),
                        debit_account=AccountHead.objects.get(name="CASH" if payment_mode == "CASH" else "BANK"),
                        credit_account=due.fee_type.account_head,
                        amount=Decimal(alloc),
                        remarks=f"{student.full_name} - {due.fee_type.name} ({due.month.strftime('%B %Y')})",
                        school=student.school
                    )

                    total_allocated += Decimal(alloc)

                remaining -= Decimal(alloc)

            advance_obj.advance_amount = remaining
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
        'month': month_date,
        'dues': dues,
        'advance': advance_amount,
        'step': 'entry',
        'total_due': total_due,
    })


from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import StudentFeePayment
import os

def download_receipt(request, payment_id):
    payment = StudentFeePayment.objects.select_related('student').prefetch_related('details__fee_type').get(id=payment_id)
    template_path = 'fees/fee_receipt.html'
    context = {
        'payment': payment,
        'student': payment.student,
        'details': payment.details.all(),
        'school_name': 'My School Name',  # Can be customized later
        'logo_url': os.path.join('static', 'school_logo.png'),  # optional
        'copy_types': ['Student', 'Office'],  # For duplicate receipts
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="receipt_{payment.student.full_name}_{payment.month.strftime("%Y_%m")}.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had errors rendering PDF', status=500)
    return response






