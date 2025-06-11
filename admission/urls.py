from django.urls import path
from . import views

urlpatterns = [
    path('admit/', views.admit_student, name='admit_student'),
]
