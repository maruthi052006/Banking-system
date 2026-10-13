from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, UserUpdateForm
from .models import Account, Transaction, Notification

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Create account for customer
            if user.role == 'customer':
                account = Account.objects.create(user=user)
                messages.success(request, f'Account created successfully! Your account number is {account.account_number}')
            
            # Log the user in after registration
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    
    if user.role == 'customer':
        return redirect('customer_dashboard')
    elif user.role == 'officer':
        return redirect('officer_dashboard')
    elif user.role == 'manager':
        return redirect('manager_dashboard')
    
    return redirect('home')

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})

def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('logout_success')
    
    # If GET request, show confirmation page
    return render(request, 'accounts/logout_confirm.html')

def logout_success(request):
    return render(request, 'accounts/logout.html')