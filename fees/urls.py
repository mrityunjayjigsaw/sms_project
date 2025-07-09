from django.urls import path
from .views import *

urlpatterns = [
    path('', fees_home, name='fees_home'),
    path('fee-types/add/', add_fee_type, name='add_fee_type'),
    path('fee-types/', fee_type_list, name='fee_type_list'),
    path('assign-fee-plan-bulk/', assign_fee_plan_bulk, name='assign_fee_plan_bulk'),
    path('post-fees/', assign_fees_bulk, name='assign_fees_bulk'),
    path('view-remaining-dues/', view_remaining_due_detail, name='view_remaining_due_detail'),
    path('view_remaining_due_by_student', view_remaining_due_by_student, name='view_remaining_due_by_student'),
    path('view-posted-fees/', view_posted_fees, name='view_posted_fees'),
    path('view-posted-fees-by-student/', view_posted_fees_by_student, name='view_posted_fees_by_student'),
    path('fee-collection/', fee_collection_filter, name='fee_collection_filter'),
    path('collect-fee/<int:student_id>/<str:payment_date>/', collect_fee_step2, name='collect_fee_step2'),
    path('download-receipt/<int:payment_id>/', download_receipt, name='download_receipt'),
    path('classwise-total-dues/', classwise_total_dues, name='classwise_total_dues'),
    path('student-ledger/list/', list_students_for_ledger, name='student_ledger_list'),
    path('student-ledger/<int:student_id>/', student_ledger, name='student_ledger'),  # Next step
    path('student-ledger/<int:student_id>/export/', export_student_ledger_excel, name='export_student_ledger'),

]
