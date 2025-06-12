from django.urls import path
from . import views

urlpatterns = [
    path('', views.admission_home, name='admission_home'),
    path('admit/', views.admit_student, name='admit_student'),
    path('list/', views.student_list, name='student_list'),
    path('add_class/', views.add_class, name='add_class'),
    path('add_year/', views.add_academic_year, name='add_academic_year'),
    path('class_list/', views.class_list, name='class_list'),
    path('year_list/', views.academic_year_list, name='year_list'),
    path('edit_class/<int:class_id>/', views.edit_class, name='edit_class'),
    path('delete_class/<int:class_id>/', views.delete_class, name='delete_class'),
    path('edit_year/<int:year_id>/', views.edit_year, name='edit_year'),
    path('delete_year/<int:year_id>/', views.delete_year, name='delete_year'),
    path('assign_class_year/<int:student_id>/', views.assign_class_year, name='assign_class_year'),
    path('student/<int:student_id>/records/', views.view_academic_records, name='view_academic_records'),
    path('student/<int:student_id>/profile/', views.student_profile, name='student_profile'),
    path('student/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('student/<int:student_id>/soft_delete/', views.soft_delete_student, name='soft_delete_student'),
    # path('bulk-upload-excel/', views.bulk_upload_students_excel, name='bulk_upload_excel'),
    path('download-template/', views.download_excel_template, name='download_excel_template'),
    
    path('import_students_excel/', views.import_students_excel, name='import_students_excel'),


]
