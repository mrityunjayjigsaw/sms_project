from django.urls import path
from .views import add_fee_type, fee_type_list, fees_home, assign_fee_plan_bulk, assign_fees_bulk

urlpatterns = [
    path('', fees_home, name='fees_home'),
    path('fee-types/add/', add_fee_type, name='add_fee_type'),
    path('fee-types/', fee_type_list, name='fee_type_list'),
    path('assign-fee-plan-bulk/', assign_fee_plan_bulk, name='assign_fee_plan_bulk'),
    path('post-fees/', assign_fees_bulk, name='assign_fees_bulk'),
]
