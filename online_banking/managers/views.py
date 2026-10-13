from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Account, Transaction, Notification
from officers.forms import AccountApprovalForm

@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Overall statistics
    total_customers = User.objects.filter(role='customer').count()
    total_officers = User.objects.filter(role='officer').count()
    total_accounts = Account.objects.filter(is_active=True).count()
    
    # Financial statistics
    total_deposits = Transaction.objects.filter(
        transaction_type='deposit', 
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal', 
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_balance = Account.objects.aggregate(total=Sum('balance'))['total'] or 0
    
    # Recent activities
    recent_transactions = Transaction.objects.select_related('account', 'account__user').order_by('-created_at')[:10]
    pending_approvals = Account.objects.filter(is_active=False).count()
    
    # Monthly performance data (last 6 months)
    from datetime import datetime
    monthly_data = []
    for i in range(5, -1, -1):
        month = timezone.now() - timedelta(days=30*i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            month_end = timezone.now()
        
        monthly_transactions = Transaction.objects.filter(
            created_at__range=[month_start, month_end],
            status='completed'
        )
        
        monthly_deposits = monthly_transactions.filter(transaction_type='deposit').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        monthly_withdrawals = monthly_transactions.filter(transaction_type='withdrawal').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        new_customers = User.objects.filter(
            role='customer',
            date_joined__range=[month_start, month_end]
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'deposits': float(monthly_deposits),
            'withdrawals': float(monthly_withdrawals),
            'new_customers': new_customers,
            'revenue': float(monthly_deposits - monthly_withdrawals)
        })
    
    context = {
        'total_customers': total_customers,
        'total_officers': total_officers,
        'total_accounts': total_accounts,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_balance': total_balance,
        'recent_transactions': recent_transactions,
        'pending_approvals': pending_approvals,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'managers/dashboard.html', context)

@login_required
def officer_management(request):
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    officers = User.objects.filter(role='officer')
    
    # Add performance metrics to each officer
    for officer in officers:
        officer.approved_accounts = Account.objects.filter(
            is_active=True
        ).count()  # This would need to track who approved
    
    return render(request, 'managers/officer_management.html', {
        'officers': officers
    })

@login_required
def branch_analytics(request):
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Customer growth data (last 12 months)
    growth_data = []
    for i in range(11, -1, -1):
        month = timezone.now() - timedelta(days=30*i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            month_end = timezone.now()
        
        new_customers = User.objects.filter(
            role='customer',
            date_joined__range=[month_start, month_end]
        ).count()
        
        total_customers = User.objects.filter(
            role='customer',
            date_joined__lte=month_end
        ).count()
        
        growth_data.append({
            'month': month_start.strftime('%b %Y'),
            'new_customers': new_customers,
            'total_customers': total_customers
        })
    
    # Transaction statistics
    transaction_stats = Transaction.objects.filter(
        status='completed'
    ).values('transaction_type').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    )
    
    # Account type distribution
    account_stats = Account.objects.filter(
        is_active=True
    ).values('account_type').annotate(
        count=Count('id'),
        total_balance=Sum('balance')
    )
    
    context = {
        'growth_data': growth_data,
        'transaction_stats': list(transaction_stats),
        'account_stats': list(account_stats),
    }
    
    return render(request, 'managers/branch_analytics.html', context)

@login_required
def financial_reports(request):
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Generate comprehensive financial report
    from datetime import datetime, timedelta
    
    # Last 30 days report
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    period_transactions = Transaction.objects.filter(
        created_at__range=[start_date, end_date],
        status='completed'
    )
    
    deposits = period_transactions.filter(transaction_type='deposit').aggregate(
        total=Sum('amount'), count=Count('id')
    )
    
    withdrawals = period_transactions.filter(transaction_type='withdrawal').aggregate(
        total=Sum('amount'), count=Count('id')
    )
    
    transfers = period_transactions.filter(transaction_type='transfer').aggregate(
        total=Sum('amount'), count=Count('id')
    )
    
    new_accounts = Account.objects.filter(
        created_at__range=[start_date, end_date],
        is_active=True
    ).count()
    
    report_data = {
        'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        'deposits': deposits,
        'withdrawals': withdrawals,
        'transfers': transfers,
        'new_accounts': new_accounts,
        'net_flow': (deposits['total'] or 0) - (withdrawals['total'] or 0),
    }
    
    return render(request, 'managers/financial_reports.html', {
        'report_data': report_data
    })

@login_required
def large_transactions(request):
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Transactions over $10,000 for review
    large_transactions = Transaction.objects.filter(
        amount__gte=10000,
        status='review'
    ).select_related('account', 'account__user')
    
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            
            if action == 'approve':
                transaction.status = 'completed'
                messages.success(request, 'Large transaction approved.')
            elif action == 'reject':
                transaction.status = 'failed'
                messages.success(request, 'Large transaction rejected.')
            
            transaction.save()
            
            # Notify customer
            Notification.objects.create(
                user=transaction.account.user,
                title='Large Transaction Update',
                message=f'Your large transaction of ${transaction.amount} has been {transaction.get_status_display()}. {notes}'
            )
            
        except Transaction.DoesNotExist:
            messages.error(request, 'Transaction not found.')
        
        return redirect('large_transactions')
    
    return render(request, 'managers/large_transactions.html', {
        'large_transactions': large_transactions
    })

@login_required
def dashboard_data(request):
    if request.user.role != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Data for charts
    monthly_data = []
    for i in range(5, -1, -1):
        month = timezone.now() - timedelta(days=30*i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            month_end = timezone.now()
        
        monthly_transactions = Transaction.objects.filter(
            created_at__range=[month_start, month_end],
            status='completed'
        )
        
        deposits = monthly_transactions.filter(transaction_type='deposit').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        withdrawals = monthly_transactions.filter(transaction_type='withdrawal').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'deposits': float(deposits),
            'withdrawals': float(withdrawals),
            'revenue': float(deposits - withdrawals)
        })
    
    return JsonResponse({
        'monthly_data': monthly_data
    })