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

