from django.contrib import admin
from core.models import School, UserProfile

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'is_active']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'is_admin']
    
from .models import AcademicYear, Class

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current', 'school']
    list_filter = ['is_current', 'school']
    search_fields = ['name']
    ordering = ['-start_date']

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream', 'is_active', 'school']
    list_filter = ['stream', 'school']
    search_fields = ['name']

from django.contrib import admin
from .models import StudentAdmission, StudentAcademicRecord, Class, AcademicYear

@admin.register(StudentAdmission)
class StudentAdmissionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'admission_no', 'school', 'gender', 'date_of_birth', 'is_active')
    search_fields = ('full_name', 'admission_no')
    list_filter = ('gender', 'is_active', 'category', 'religion')
    ordering = ('admission_no',)

@admin.register(StudentAcademicRecord)
class StudentAcademicRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'class_enrolled', 'section', 'is_promoted')
    list_filter = ('academic_year', 'class_enrolled', 'is_promoted')

