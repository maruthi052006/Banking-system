from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
import csv
from accounts.models import Account, Transaction, Notification
from .forms import DepositForm, WithdrawalForm, TransferForm

@login_required
def customer_dashboard(request):
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    account = Account.objects.get(user=request.user)
    transactions = Transaction.objects.filter(account=account)[:5]
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    
    # Statistics for charts
    monthly_stats = Transaction.objects.filter(
        account=account,
        status='completed'
    ).extra({
        'month': "strftime('%%Y-%%m', created_at)"
    }).values('month', 'transaction_type').annotate(
        total=Sum('amount')
    )
    
    context = {
        'account': account,
        'transactions': transactions,
        'notifications': notifications,
        'monthly_stats': list(monthly_stats),
    }
    
    return render(request, 'customers/dashboard.html', context)

@login_required
def deposit(request):
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    account = Account.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']
            
            # Create transaction
            transaction = Transaction.objects.create(
                account=account,
                transaction_type='deposit',
                amount=amount,
                description=description,
                status='completed'
            )
            
            # Update account balance
            account.balance += amount
            account.save()
            
            messages.success(request, f'Successfully deposited ${amount}')
            return redirect('customer_dashboard')
    else:
        form = DepositForm()
    
    return render(request, 'customers/deposit.html', {'form': form})

@login_required
def withdrawal(request):
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    account = Account.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']
            
            if account.balance >= amount:
                # Create transaction
                transaction = Transaction.objects.create(
                    account=account,
                    transaction_type='withdrawal',
                    amount=amount,
                    description=description,
                    status='completed'
                )
                
                # Update account balance
                account.balance -= amount
                account.save()
                
                messages.success(request, f'Successfully withdrew ${amount}')
                return redirect('customer_dashboard')
            else:
                messages.error(request, 'Insufficient funds.')
    else:
        form = WithdrawalForm()
    
    return render(request, 'customers/withdrawal.html', {'form': form})

@login_required
def transfer(request):
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    account = Account.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            recipient_account_number = form.cleaned_data['recipient_account_number']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']
            
            try:
                recipient_account = Account.objects.get(account_number=recipient_account_number, is_active=True)
                
                if account.balance >= amount:
                    # Create transaction for sender
                    Transaction.objects.create(
                        account=account,
                        transaction_type='transfer',
                        amount=amount,
                        description=f"Transfer to {recipient_account_number}: {description}",
                        recipient_account=recipient_account,
                        status='completed'
                    )
                    
                    # Create transaction for recipient
                    Transaction.objects.create(
                        account=recipient_account,
                        transaction_type='deposit',
                        amount=amount,
                        description=f"Transfer from {account.account_number}: {description}",
                        status='completed'
                    )
                    
                    # Update balances
                    account.balance -= amount
                    account.save()
                    
                    recipient_account.balance += amount
                    recipient_account.save()
                    
                    messages.success(request, f'Successfully transferred ${amount} to {recipient_account_number}')
                    return redirect('customer_dashboard')
                else:
                    messages.error(request, 'Insufficient funds.')
            except Account.DoesNotExist:
                messages.error(request, 'Recipient account not found.')
    else:
        form = TransferForm()
    
    return render(request, 'customers/transfer.html', {'form': form})

@login_required
def transaction_history(request):
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    account = Account.objects.get(user=request.user)
    transactions = Transaction.objects.filter(account=account)
    
    return render(request, 'customers/transaction_history.html', {'transactions': transactions})

@login_required
def download_statement(request, format_type):
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    account = Account.objects.get(user=request.user)
    transactions = Transaction.objects.filter(account=account)
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="statement_{account.account_number}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Type', 'Amount', 'Description', 'Status'])
        
        for transaction in transactions:
            writer.writerow([
                transaction.created_at,
                transaction.get_transaction_type_display(),
                transaction.amount,
                transaction.description,
                transaction.get_status_display()
            ])
        
        return response
    
    elif format_type == 'pdf':
        # PDF generation logic would go here
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="statement_{account.account_number}.pdf"'
        
        # Simple PDF implementation
        p = canvas.Canvas(response)
        p.drawString(100, 800, f"Account Statement - {account.account_number}")
        p.drawString(100, 780, f"Customer: {account.user.get_full_name()}")
        p.drawString(100, 760, f"Balance: ${account.balance}")
        
        y = 740
        for transaction in transactions[:20]:  # Limit to 20 transactions
            p.drawString(100, y, f"{transaction.created_at} - {transaction.transaction_type} - ${transaction.amount}")
            y -= 20
        
        p.showPage()
        p.save()
        return response
    
    
from django.core.paginator import Paginator

@login_required
def transaction_history(request):
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    account = Account.objects.get(user=request.user)
    transactions_list = Transaction.objects.filter(account=account)
    
    paginator = Paginator(transactions_list, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    
    return render(request, 'customers/transaction_history.html', {
        'transactions': transactions,
        'account': account
    })