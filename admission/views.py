from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import StudentAdmissionForm, ClassForm, AcademicYearForm
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
