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

    # Generate admission_no in advance
    last_student = StudentAdmission.objects.filter(school=school).order_by('id').last()
    if last_student:
        last_id = int(last_student.admission_no.replace('ADM', ''))
        next_adm_no = f"ADM{last_id + 1:04d}"
    else:
        next_adm_no = "ADM0001"

    if request.method == 'POST':
        form = StudentAdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = school
            student.admission_no = next_adm_no  # still enforced here
            student.save()
            return redirect('student_list')
    else:
        form = StudentAdmissionForm(initial={'admission_no': next_adm_no})

    return render(request, 'admission/admit_student.html', {'form': form})

@login_required
def student_list(request):
    school = request.user.userprofile.school
    students = StudentAdmission.objects.filter(school=school, is_active=True)

    # Filters
    class_id = request.GET.get('class_id')
    year_id = request.GET.get('year_id')
    name_query = request.GET.get('name')

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
def assign_class_year(request, student_id):
    student = StudentAdmission.objects.get(id=student_id)
    school = request.user.userprofile.school

    # Check if student already has an academic record for this year (optional)
    existing_record = StudentAcademicRecord.objects.filter(student=student, school=school).last()

    form = StudentAcademicRecordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.student = student
        record.school = school
        record.save()
        return redirect('student_list')

    return render(request, 'admission/assign_class_year.html', {
        'form': form,
        'student': student,
        'existing_record': existing_record
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
