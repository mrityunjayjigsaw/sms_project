# transactions/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.transactions_home, name='transactions_home'), 
    path('add/', views.add_manual_transaction, name='add_manual_transaction'),
    path('view/', views.view_transactions, name='view_transactions'), 
    # transactions/urls.py
    path('export/', views.export_transactions_excel, name='export_transactions_excel'),

]
