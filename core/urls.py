from django.urls import path
from core import views
urlpatterns = [
    path('school_signup/', views.school_signup, name='school_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.public_home, name='public_home'),
    path('home/', views.home, name='home'),
]
