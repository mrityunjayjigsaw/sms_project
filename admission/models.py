from django.db import models
from core.models import School
from django.utils import timezone

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

CATEGORY_CHOICES = [
    ('GEN', 'General'),
    ('OBC', 'OBC'),
    ('SC', 'SC'),
    ('ST', 'ST'),
]

RELIGION_CHOICES = [
    ('Hindu', 'Hindu'),
    ('Muslim', 'Muslim'),
    ('Christian', 'Christian'),
    ('Sikh', 'Sikh'),
    ('Other', 'Other'),
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
    admission_date = models.DateField(default=timezone.now)

    father_name = models.CharField(max_length=255, blank=True, default='', null=True)
    mother_name = models.CharField(max_length=255, blank=True, default='', null=True)
    father_profession = models.CharField(max_length=255, blank=True, default='', null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='GEN')
    religion = models.CharField(max_length=50, choices=RELIGION_CHOICES, default='Hindu')
    aadhar_no = models.CharField(max_length=20, blank=True, null=True)
    apaar_id = models.CharField(max_length=20, blank=True, null=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_no = models.CharField(max_length=15, blank=True, null=True)

    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    address = models.TextField(blank=True, default='', null=True)
    email = models.EmailField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.full_name} ({self.admission_no})"


class StudentAcademicRecord(models.Model):
    # Each row = One student in one academic year, same student can have multiple records for different years
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
