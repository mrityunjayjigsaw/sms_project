from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def reports_home(request):
    return render(request, 'reports/reports_home.html')


# reports/views.py
from admission.models import *
from django.contrib.auth.decorators import login_required

@login_required
def student_list_report(request):
    user_school = request.user.userprofile.school
    academic_year = request.GET.get('academic_year')
    class_id = request.GET.get('class_id')

    academic_years = AcademicYear.objects.filter(school=user_school)
    classes = Class.objects.filter(school=user_school)

    records = StudentAcademicRecord.objects.filter(school=user_school).select_related('student', 'academic_year', 'class_enrolled')

    if academic_year:
        records = records.filter(academic_year_id=academic_year)
    if class_id:
        records = records.filter(class_enrolled_id=class_id)

    return render(request, 'reports/admission/student_list_report.html', {
        'records': records,
        'academic_years': academic_years,
        'classes': classes,
        'selected_year': academic_year,
        'selected_class': class_id,
    })



# reports/views.py (continued)
import openpyxl
from django.http import HttpResponse
from django.utils.dateparse import parse_date

@login_required
def export_student_list_report(request):
    user_school = request.user.userprofile.school
    academic_year = request.GET.get('academic_year')
    class_id = request.GET.get('class_id')

    records = StudentAcademicRecord.objects.filter(school=user_school).select_related('student', 'academic_year', 'class_enrolled')
    if academic_year:
        records = records.filter(academic_year_id=academic_year)
    if class_id:
        records = records.filter(class_enrolled_id=class_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student List"

    ws.append(['Admission No', 'Full Name', 'Gender', 'Class', 'Academic Year', 'Mobile No'])

    for r in records:
        s = r.student
        ws.append([
            s.admission_no,
            s.full_name,
            s.gender,
            r.class_enrolled.name if r.class_enrolled else '',
            r.academic_year.name if r.academic_year else '',
            s.mobile_no
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="student_list.xlsx"'
    wb.save(response)
    return response

# reports/views.py
from fees.models import StudentFeeDue

from calendar import month_name
import calendar

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from fees.models import StudentFeeDue, StudentFeePaymentDetail
from django.db.models import Sum
import calendar

@login_required
def fee_defaulter_report(request):
    user_school = request.user.userprofile.school
    academic_year = request.GET.get('academic_year')
    class_id = request.GET.get('class_id')
    month_str = request.GET.get('month')

    academic_years = AcademicYear.objects.filter(school=user_school)
    classes = Class.objects.filter(school=user_school)

    # Safely convert to int if present
    year_id = int(academic_year) if academic_year and academic_year.isdigit() else None
    class_id_val = int(class_id) if class_id and class_id.isdigit() else None

    dues = StudentFeeDue.objects.select_related('student', 'fee_type').filter(student__school=user_school)

    if year_id:
        dues = dues.filter(student__academic_records__academic_year_id=year_id)
    if class_id_val:
        dues = dues.filter(student__academic_records__class_enrolled_id=class_id_val)
    if month_str:
        dues = dues.filter(month__month=int(month_str))

    defaulters = []
    for due in dues:
        paid = StudentFeePaymentDetail.objects.filter(
            payment__student=due.student,
            payment__month=due.month,
            fee_type=due.fee_type
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        balance = due.amount_due - paid
        if balance > 0:
            # Fetch correct academic record
            record_filter = {}
            if year_id:
                record_filter['academic_year_id'] = year_id
            if class_id_val:
                record_filter['class_enrolled_id'] = class_id_val

            academic_record = due.student.academic_records.filter(**record_filter).first()

            defaulters.append({
                'student': due.student,
                'class': academic_record.class_enrolled.name if academic_record else '',
                'month': due.month.strftime('%B %Y'),
                'fee_type': due.fee_type.name,
                'due': due.amount_due,
                'paid': paid,
                'balance': balance,
            })

    return render(request, 'reports/fees/fee_defaulter_report.html', {
        'dues': defaulters,
        'academic_years': academic_years,
        'classes': classes,
        'selected_year': academic_year,
        'selected_class': class_id,
        'selected_month': month_str,
    })



import openpyxl
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from fees.models import StudentFeeDue, StudentFeePaymentDetail
from django.db.models import Sum

@login_required
def export_fee_defaulter_report(request):
    user_school = request.user.userprofile.school
    academic_year = request.GET.get('academic_year')
    class_id = request.GET.get('class_id')
    month_str = request.GET.get('month')

    # Safe conversion
    year_id = int(academic_year) if academic_year and academic_year.isdigit() else None
    class_id_val = int(class_id) if class_id and class_id.isdigit() else None

    dues = StudentFeeDue.objects.select_related('student', 'fee_type').filter(student__school=user_school)

    if year_id:
        dues = dues.filter(student__academic_records__academic_year_id=year_id)
    if class_id_val:
        dues = dues.filter(student__academic_records__class_enrolled_id=class_id_val)
    if month_str:
        dues = dues.filter(month__month=int(month_str))

    rows = []
    for due in dues:
        paid = StudentFeePaymentDetail.objects.filter(
            payment__student=due.student,
            payment__month=due.month,
            fee_type=due.fee_type
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        balance = due.amount_due - paid
        if balance > 0:
            # Fetch academic record to get class
            record_filter = {}
            if year_id:
                record_filter['academic_year_id'] = year_id
            if class_id_val:
                record_filter['class_enrolled_id'] = class_id_val

            academic_record = due.student.academic_records.filter(**record_filter).first()
            class_name = academic_record.class_enrolled.name if academic_record else ''

            rows.append([
                due.student.full_name,
                class_name,
                due.month.strftime('%B %Y'),
                due.fee_type.name,
                float(due.amount_due),
                float(paid),
                float(balance)
            ])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fee Defaulters"

    ws.append(['Student', 'Class', 'Month', 'Fee Type', 'Due (₹)', 'Paid (₹)', 'Balance (₹)'])
    for row in rows:
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="fee_defaulters.xlsx"'
    wb.save(response)
    return response


