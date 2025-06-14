# transactions/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ManualTransactionForm
from .models import Transaction
from django.contrib.auth.decorators import login_required
from admission.models import School 

@login_required
def transactions_home(request):
    return render(request, 'transactions/transactions_home.html')

@login_required
def add_manual_transaction(request):
     # adjust import if needed

    user_school = request.user.userprofile.school
    form = ManualTransactionForm(request.POST or None)
    form.fields['debit_account'].queryset = form.fields['debit_account'].queryset.filter(school=user_school)
    form.fields['credit_account'].queryset = form.fields['credit_account'].queryset.filter(school=user_school)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data

        if cd['debit_account'] == cd['credit_account']:
            messages.error(request, "Debit and Credit accounts cannot be the same.")
            return render(request, 'transactions/add_manual_transaction.html', {'form': form})

        Transaction.objects.create(
            date=cd['date'],
            debit_account=cd['debit_account'],
            credit_account=cd['credit_account'],
            amount=cd['amount'],
            remarks=cd['remarks'],
            voucher_type=cd['voucher_type'],
            school=user_school,
            created_by=request.user
        )
        messages.success(request, "Transaction recorded successfully.")
        return redirect('add_manual_transaction')

    return render(request, 'transactions/add_manual_transaction.html', {'form': form})


# transactions/views.py
from django.db.models import Q
from django.utils.dateparse import parse_date
from .models import Transaction, AccountHead
from django.contrib.auth.decorators import login_required

@login_required
def view_transactions(request):
    user_school = request.user.userprofile.school
    transactions = Transaction.objects.filter(school=user_school).order_by('-date')

    # Filters
    account_id = request.GET.get('account')
    voucher_type = request.GET.get('voucher_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if account_id and account_id.isdigit():
        transactions = transactions.filter(
            Q(debit_account_id=account_id) | Q(credit_account_id=account_id)
        )
    if voucher_type:
        transactions = transactions.filter(voucher_type=voucher_type)
    parsed_start = parse_date(start_date)
    if parsed_start:
        transactions = transactions.filter(date__gte=parsed_start)

    parsed_end = parse_date(end_date)
    if parsed_end:
        transactions = transactions.filter(date__lte=parsed_end)


    accounts = AccountHead.objects.filter(school=user_school)

    return render(request, 'transactions/view_transactions.html', {
        'transactions': transactions,
        'accounts': accounts,
        'voucher_type_filter': voucher_type,
        'account_filter': account_id,
        'start_date': start_date,
        'end_date': end_date,
    })


# transactions/views.py
import openpyxl
from django.http import HttpResponse
from django.db.models import Q
from django.utils.dateparse import parse_date
from .models import Transaction, AccountHead

@login_required
def export_transactions_excel(request):
    user_school = request.user.userprofile.school
    transactions = Transaction.objects.filter(school=user_school).order_by('-date')

    # Apply filters (same as in view_transactions)
    account_id = request.GET.get('account')
    voucher_type = request.GET.get('voucher_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if account_id and account_id.isdigit():
        transactions = transactions.filter(
            Q(debit_account_id=account_id) | Q(credit_account_id=account_id)
        )
    if voucher_type:
        transactions = transactions.filter(voucher_type=voucher_type)
        
    parsed_start = parse_date(start_date)
    if parsed_start:
        transactions = transactions.filter(date__gte=parsed_start)

    parsed_end = parse_date(end_date)
    if parsed_end:
        transactions = transactions.filter(date__lte=parsed_end)


    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"

    # Header
    ws.append(['Date', 'Debit Account', 'Credit Account', 'Amount', 'Voucher Type', 'Remarks'])

    # Data rows
    for txn in transactions:
        ws.append([
            txn.date.strftime('%Y-%m-%d'),
            txn.debit_account.name,
            txn.credit_account.name,
            float(txn.amount),
            txn.get_voucher_type_display(),
            txn.remarks or ''
        ])

    # Set response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'
    wb.save(response)
    return response
