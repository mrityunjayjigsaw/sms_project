from django.db import models
from core.models import School

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

class AcademicYear(models.Model):
    name = models.CharField(max_length=10)  # e.g., "2024-25"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Class(models.Model):
    name = models.CharField(max_length=50)  # e.g., "Class 10", "12 Arts"
    stream = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class StudentAdmission(models.Model):
    admission_no = models.CharField(max_length=20, unique=True)
    ssr_no = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    parent_name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    admission_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.full_name} ({self.admission_no})"


class StudentAcademicRecord(models.Model):
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE, related_name='academic_records')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    class_enrolled = models.ForeignKey(Class, on_delete=models.CASCADE)
    section = models.CharField(max_length=5, blank=True, null=True)
    is_promoted = models.BooleanField(default=False)
    promoted_to = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='promoted_students')
    remarks = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student.full_name} - {self.academic_year.name}"
