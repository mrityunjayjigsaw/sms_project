# transactions/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.transactions_home, name='transactions_home'), 
    path('add/', views.add_manual_transaction, name='add_manual_transaction'),
    path('view/', views.view_transactions, name='view_transactions'), 
    # transactions/urls.py
    path('export/', views.export_transactions_excel, name='export_transactions_excel'),
    # transactions/urls.py
    path('ledger/', views.ledger_view, name='ledger_view'),
    # transactions/urls.py
    path('ledger/export/', views.export_ledger_excel, name='export_ledger_excel'),
    # transactions/urls.py
    path('opening-balances/', views.set_opening_balances, name='set_opening_balances'),




]
