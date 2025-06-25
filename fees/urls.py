from django.urls import path
from .views import *

urlpatterns = [
    path('', fees_home, name='fees_home'),
    path('fee-types/add/', add_fee_type, name='add_fee_type'),
    path('fee-types/', fee_type_list, name='fee_type_list'),
    path('assign-fee-plan-bulk/', assign_fee_plan_bulk, name='assign_fee_plan_bulk'),
    path('post-fees/', assign_fees_bulk, name='assign_fees_bulk'),
    path('view-posted-fees/', view_posted_fees_detail, name='view_posted_fees_detail'),
    path('fee-collection/', fee_collection_filter, name='fee_collection_filter'),
    path('collect-fee/<int:student_id>/<str:month_str>/', collect_fee_step2, name='collect_fee_step2'),
    path('download-receipt/<int:payment_id>/', download_receipt, name='download_receipt'),
    path('view-posted-fees/student/', view_posted_fees_by_student, name='view_posted_fees_by_student'),
]
