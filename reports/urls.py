from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    # Next: student_list_report
    path('', views.reports_home, name='reports_home'),
    path('admission/student-list/', views.student_list_report, name='student_list_report'),
    path('admission/student-list/export/', views.export_student_list_report, name='export_student_list_report'),
    # reports/urls.py
    path('fees/defaulters/', views.fee_defaulter_report, name='fee_defaulter_report'),
    path('fees/defaulters/export/', views.export_fee_defaulter_report, name='export_fee_defaulter_report'),
    

]

