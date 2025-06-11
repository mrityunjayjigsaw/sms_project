from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import StudentAdmissionForm
from .models import StudentAdmission
from core.models import UserProfile
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

@login_required
def admit_student(request):
    if request.method == 'POST':
        form = StudentAdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)

            # Get the current user's school
            student.school = request.user.userprofile.school

            # Generate auto admission number (ADM0001...)
            last_student = StudentAdmission.objects.filter(school=student.school).order_by('id').last()
            if last_student:
                last_id = int(last_student.admission_no.replace('ADM', ''))
                new_id = f"ADM{last_id + 1:04d}"
            else:
                new_id = "ADM0001"
            student.admission_no = new_id

            student.save()
            return redirect('student_list')  # Replace with your list view
    else:
        form = StudentAdmissionForm()

    return render(request, 'admission/admit_student.html', {'form': form})
