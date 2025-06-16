from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import StudentAdmissionForm, ClassForm, AcademicYearForm, StudentAcademicRecordForm
from .models import StudentAdmission, StudentAcademicRecord, Class, AcademicYear
from core.models import UserProfile
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now


@login_required
def admission_home(request):
    return render(request, 'admission/admission_home.html')


@login_required
def admit_student(request):
    school = request.user.userprofile.school

    # Generate next numeric admission_no
    last_student = StudentAdmission.objects.filter(school=school).order_by('-id').first()
    if last_student and last_student.admission_no.isdigit():
        last_adm_no = int(last_student.admission_no)
        next_adm_no = str(last_adm_no + 1)
    else:
        next_adm_no = '1001'  # Start from 1001 if no student or non-numeric

    if request.method == 'POST':
        form = StudentAdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = school
            student.admission_no = next_adm_no  # use numeric admission no
            student.is_active = True  # ensure active on manual admit
            student.save()
            
            academic_year = form.cleaned_data['academic_year']
            class_enrolled = form.cleaned_data['class_enrolled']
            section = form.cleaned_data.get('section', '')

            StudentAcademicRecord.objects.create(
                student=student,
                academic_year=academic_year,
                class_enrolled=class_enrolled,
                section=section,
                school=school
            )
            
            return redirect('student_list')
    else:
        form = StudentAdmissionForm(initial={'admission_no': next_adm_no})

    return render(request, 'admission/admit_student.html', {'form': form})

@login_required
def student_list(request):
    school = request.user.userprofile.school
    if request.user.is_superuser:
        students = StudentAdmission.objects.filter(is_active=True)
        print("Found students:", students) 
    else:
        students = StudentAdmission.objects.filter(
        school=school,
        is_active=True
        )
    
    # Filters
    class_id = request.GET.get('class_id')
    year_id = request.GET.get('year_id')
    name_query = request.GET.get('name',"")

    academic_records = StudentAcademicRecord.objects.filter(school=school)

    if class_id:
        academic_records = academic_records.filter(class_enrolled_id=class_id)

    if year_id:
        academic_records = academic_records.filter(academic_year_id=year_id)

    if name_query:
        students = students.filter(full_name__icontains=name_query)

    # Match academic records with students
    student_ids = academic_records.values_list('student_id', flat=True)
    students = students.filter(id__in=student_ids)

    classes = Class.objects.filter(school=school, is_active=True)
    years = AcademicYear.objects.filter(school=school)

    return render(request, 'admission/student_list.html', {
        'students': students,
        'classes': classes,
        'years': years,
        'selected_class': class_id,
        'selected_year': year_id,
        'name_query': name_query
    })

@login_required
def add_class(request):
    form = ClassForm(request.POST or None)
    if form.is_valid():
        cls = form.save(commit=False)
        cls.school = request.user.userprofile.school
        cls.save()
        return redirect('admission_home')
    return render(request, 'admission/add_class.html', {'form': form})


@login_required
def add_academic_year(request):
    form = AcademicYearForm(request.POST or None)
    if form.is_valid():
        year = form.save(commit=False)
        year.school = request.user.userprofile.school
        year.save()
        return redirect('admission_home')
    return render(request, 'admission/add_academic_year.html', {'form': form})

@login_required
def class_list(request):
    school = request.user.userprofile.school
    classes = Class.objects.filter(school=school)
    return render(request, 'admission/class_list.html', {'classes': classes})


@login_required
def academic_year_list(request):
    school = request.user.userprofile.school
    years = AcademicYear.objects.filter(school=school)
    return render(request, 'admission/academic_year_list.html', {'years': years})

@login_required
def edit_class(request, class_id):
    school = request.user.userprofile.school
    cls = Class.objects.get(id=class_id, school=school)
    form = ClassForm(request.POST or None, instance=cls)
    if form.is_valid():
        form.save()
        return redirect('class_list')
    return render(request, 'admission/edit_class.html', {'form': form})

@login_required
def delete_class(request, class_id):
    school = request.user.userprofile.school
    cls = Class.objects.get(id=class_id, school=school)
    if request.method == 'POST':
        cls.delete()
        return redirect('class_list')
    return render(request, 'admission/delete_confirm.html', {'object': cls, 'type': 'Class'})

@login_required
def edit_year(request, year_id):
    school = request.user.userprofile.school
    year = AcademicYear.objects.get(id=year_id, school=school)
    form = AcademicYearForm(request.POST or None, instance=year)
    if form.is_valid():
        form.save()
        return redirect('academic_year_list')
    return render(request, 'admission/edit_year.html', {'form': form})

@login_required
def delete_year(request, year_id):
    school = request.user.userprofile.school
    year = AcademicYear.objects.get(id=year_id, school=school)
    if request.method == 'POST':
        year.delete()
        return redirect('academic_year_list')
    return render(request, 'admission/delete_confirm.html', {'object': year, 'type': 'Academic Year'})

@login_required
def edit_student_academic_record(request, student_id):
    """
    View to edit the latest academic record of a student.
    Only used for admin corrections.
    """
    student = get_object_or_404(StudentAdmission, id=student_id)
    academic_record = student.academic_records.last()

    if not academic_record:
        return render(request, "admission/no_record_found.html", {"student": student})

    form = StudentAcademicRecordForm(request.POST or None, instance=academic_record)

    if request.method == 'POST' and form.is_valid():
        updated_record = form.save(commit=False)
        updated_record.student = student
        updated_record.school = academic_record.school  # keep original school
        updated_record.save()
        return redirect('student_list')

    return render(request, 'admission/edit_academic_record.html', {
        'form': form,
        'student': student,
        'academic_record': academic_record,
    })


from django.shortcuts import get_object_or_404 
@login_required
def view_academic_records(request, student_id):
    student = get_object_or_404(StudentAdmission, id=student_id)
    records = student.academic_records.select_related('academic_year', 'class_enrolled', 'promoted_to')

    return render(request, 'admission/view_academic_records.html', {
        'student': student,
        'records': records
    })

@login_required
def student_profile(request, student_id):
    student = get_object_or_404(StudentAdmission, id=student_id)
    records = student.academic_records.select_related('academic_year', 'class_enrolled', 'promoted_to')
    
    return render(request, 'admission/student_profile.html', {
        'student': student,
        'records': records
    })

from .forms import StudentAdmissionForm
from django.http import HttpResponseForbidden

@login_required
def edit_student(request, student_id):
    student = get_object_or_404(StudentAdmission, id=student_id)
    school = request.user.userprofile.school

    # Restrict editing only to same school
    if student.school != school:
        return HttpResponseForbidden("You don't have permission to edit this student.")

    form = StudentAdmissionForm(request.POST or None, instance=student)

    if form.is_valid():
        form.save()
        return redirect('student_profile', student_id=student.id)

    return render(request, 'admission/edit_student.html', {'form': form, 'student': student})


@login_required
def soft_delete_student(request, student_id):
    student = get_object_or_404(StudentAdmission, id=student_id)
    if request.user.userprofile.school != student.school:
        return HttpResponseForbidden("You don't have permission to delete this student.")
    
    if request.method == 'POST':
        student.is_active = False
        student.save()
        return redirect('student_list')


from django.shortcuts import render, redirect
from django.contrib import messages
from openpyxl import load_workbook
from django.utils.dateparse import parse_date
from admission.models import StudentAdmission,AcademicYear, Class, StudentAcademicRecord
from core.models import School
from datetime import datetime, date


@login_required
def import_students_excel(request):
    if request.method == 'POST' and request.FILES.get('student_file'):
        excel_file = request.FILES['student_file']
        wb = load_workbook(excel_file)
        ws = wb.active
        school = request.user.userprofile.school
        rows = list(ws.iter_rows(min_row=2, values_only=True))

        for row in rows:
            try:
                (
                    full_name, date_of_birth, gender, category,
                    religion, mobile_no, whatsapp_no, aadhar_no,
                    admission_date, father_name, mother_name, father_profession,
                    academic_year_str, class_name, section
                ) = row

                # Handle both Excel date formats and strings
                if isinstance(date_of_birth, (datetime, date)):
                    dob = date_of_birth
                else:
                    dob = parse_date(str(date_of_birth)) if date_of_birth else None

                if not dob:
                    messages.error(request, f"{full_name}: Invalid or missing date of birth.")
                    continue

                if isinstance(admission_date, (datetime, date)):
                    adm_date = admission_date
                else:
                    adm_date = parse_date(str(admission_date)) if admission_date else None

                if not adm_date:
                    messages.error(request, f"{full_name}: Invalid or missing admission date.")
                    continue

                # Look up academic year and class
                academic_year = AcademicYear.objects.get(name=academic_year_str, school=school)
                class_enrolled = Class.objects.get(name=class_name, school=school)

                # Generate admission number
                last_student = StudentAdmission.objects.filter(school=school).order_by('-id').first()
                next_adm_no = str(int(last_student.admission_no) + 1) if last_student and last_student.admission_no.isdigit() else '1001'

                # Create student
                student = StudentAdmission.objects.create(
                    full_name=full_name,
                    date_of_birth=dob,
                    gender=gender,
                    category=category,
                    religion=religion,
                    mobile_no=mobile_no,
                    whatsapp_no=whatsapp_no,
                    aadhar_no=aadhar_no,
                    admission_date=adm_date,
                    father_name=father_name,
                    mother_name=mother_name,
                    father_profession=father_profession,
                    school=school,
                    is_active=True,
                    admission_no=next_adm_no
                )

                # Create academic record
                StudentAcademicRecord.objects.create(
                    student=student,
                    academic_year=academic_year,
                    class_enrolled=class_enrolled,
                    section=section,
                    school=school
                )

                messages.success(request, f"{full_name} imported successfully.")

            except AcademicYear.DoesNotExist:
                messages.error(request, f"{full_name}: Academic Year '{academic_year_str}' not found.")
            except Class.DoesNotExist:
                messages.error(request, f"{full_name}: Class '{class_name}' not found.")
            except Exception as e:
                messages.error(request, f"{full_name}: Error importing - {str(e)}")

        return redirect('import_students_excel')

    return render(request, 'admission/import_students_excel.html')



from django.http import FileResponse
import os
from django.conf import settings
@login_required
def download_excel_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'static/admission/student_import_template.xlsx')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='student_template.xlsx')
