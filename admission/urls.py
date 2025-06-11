from django.urls import path
from . import views

urlpatterns = [
    path('', views.admission_home, name='admission_home'),
    path('admit/', views.admit_student, name='admit_student'),
    path('list/', views.student_list, name='student_list'),
    path('add_class/', views.add_class, name='add_class'),
    path('add_year/', views.add_academic_year, name='add_academic_year'),


]
