from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import BulkFeePlanForm
from admission.models import StudentAcademicRecord
from .models import FeeType, StudentFeePlan
from django.db import transaction
from django.shortcuts import render, redirect
from .forms import PostingFeesForm

from .models import StudentFeePlan, FeeType, StudentFeeDue
from transactions.models import Transaction, AccountHead
from datetime import date, timedelta
# Create your views here.
from django.shortcuts import render, redirect
from .forms import FeeTypeForm
from .models import FeeType
from django.db.models import Q


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


