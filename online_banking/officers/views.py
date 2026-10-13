from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from accounts.models import User, Account, Transaction, Notification
from .forms import AccountApprovalForm, TransactionReviewForm

@login_required
def officer_dashboard(request):
    if request.user.role != 'officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Statistics for dashboard
    total_customers = User.objects.filter(role='customer').count()
    pending_accounts = Account.objects.filter(is_active=False).count()
    pending_transactions = Transaction.objects.filter(status='review').count()
    
    # Recent activities
    recent_transactions = Transaction.objects.select_related('account', 'account__user').order_by('-created_at')[:10]
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Chart data - Transaction types for today
    from datetime import date
    today = date.today()
    transaction_stats = Transaction.objects.filter(
        created_at__date=today,
        status='completed'
    ).values('transaction_type').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    )
    
    context = {
        'total_customers': total_customers,
        'pending_accounts': pending_accounts,
        'pending_transactions': pending_transactions,
        'recent_transactions': recent_transactions,
        'recent_notifications': recent_notifications,
        'transaction_stats': list(transaction_stats),
    }
    
    return render(request, 'officers/dashboard.html', context)

@login_required
def customer_management(request):
    if request.user.role != 'officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    customers = User.objects.filter(role='customer').select_related('account')
    search_query = request.GET.get('search', '')
    
    if search_query:
        customers = customers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(account__account_number__icontains=search_query)
        )
    
    return render(request, 'officers/customer_management.html', {
        'customers': customers,
        'search_query': search_query
    })

@login_required
def account_approvals(request):
    if request.user.role != 'officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    pending_accounts = Account.objects.filter(is_active=False).select_related('user')
    
    if request.method == 'POST':
        form = AccountApprovalForm(request.POST)
        if form.is_valid():
            account_id = form.cleaned_data['account_id']
            action = form.cleaned_data['action']
            remarks = form.cleaned_data['remarks']
            
            try:
                account = Account.objects.get(id=account_id)
                
                if action == 'approve':
                    account.is_active = True
                    account.save()
                    
                    # Create notification for customer
                    Notification.objects.create(
                        user=account.user,
                        title='Account Approved',
                        message=f'Your account {account.account_number} has been approved and is now active.'
                    )
                    
                    messages.success(request, f'Account {account.account_number} approved successfully.')
                
                elif action == 'reject':
                    # In a real system, you might want to delete or mark as rejected
                    account.delete()
                    
                    messages.success(request, f'Account {account.account_number} rejected and removed.')
                
            except Account.DoesNotExist:
                messages.error(request, 'Account not found.')
            
            return redirect('account_approvals')
    
    else:
        form = AccountApprovalForm()
    
    return render(request, 'officers/account_approvals.html', {
        'pending_accounts': pending_accounts,
        'form': form
    })

@login_required
def transaction_monitoring(request):
    if request.user.role != 'officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    transactions = Transaction.objects.select_related('account', 'account__user').order_by('-created_at')
    
    # Filter options
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    return render(request, 'officers/transaction_monitoring.html', {
        'transactions': transactions,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'date_from': date_from,
        'date_to': date_to,
    })

@login_required
def review_transaction(request, transaction_id):
    if request.user.role != 'officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
    except Transaction.DoesNotExist:
        messages.error(request, 'Transaction not found.')
        return redirect('transaction_monitoring')
    
    if request.method == 'POST':
        form = TransactionReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            officer_notes = form.cleaned_data['officer_notes']
            
            if action == 'approve':
                transaction.status = 'completed'
                messages.success(request, 'Transaction approved.')
            elif action == 'reject':
                transaction.status = 'failed'
                messages.success(request, 'Transaction rejected.')
            elif action == 'review':
                transaction.status = 'review'
                messages.info(request, 'Transaction marked for review.')
            
            transaction.save()
            
            # Create notification for customer
            Notification.objects.create(
                user=transaction.account.user,
                title=f'Transaction {transaction.get_status_display()}',
                message=f'Your transaction of ${transaction.amount} has been {transaction.get_status_display()}. {officer_notes}'
            )
            
            return redirect('transaction_monitoring')
    else:
        form = TransactionReviewForm()
    
    return render(request, 'officers/review_transaction.html', {
        'transaction': transaction,
        'form': form
    })

@login_required
def send_notification(request):
    if request.user.role != 'officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        try:
            customer = User.objects.get(id=customer_id, role='customer')
            Notification.objects.create(
                user=customer,
                title=title,
                message=message
            )
            messages.success(request, 'Notification sent successfully.')
        except User.DoesNotExist:
            messages.error(request, 'Customer not found.')
        
        return redirect('customer_management')
    
    return redirect('customer_management')

@login_required
def dashboard_data(request):
    if request.user.role != 'officer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    from datetime import datetime, timedelta
    
    # Last 7 days transaction data for charts
    dates = []
    deposit_data = []
    withdrawal_data = []
    transfer_data = []
    
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
        
        deposits = Transaction.objects.filter(
            created_at__date=date,
            transaction_type='deposit',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        withdrawals = Transaction.objects.filter(
            created_at__date=date,
            transaction_type='withdrawal',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        transfers = Transaction.objects.filter(
            created_at__date=date,
            transaction_type='transfer',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        deposit_data.append(float(deposits))
        withdrawal_data.append(float(withdrawals))
        transfer_data.append(float(transfers))
    
    return JsonResponse({
        'dates': dates,
        'deposits': deposit_data,
        'withdrawals': withdrawal_data,
        'transfers': transfer_data,
    })