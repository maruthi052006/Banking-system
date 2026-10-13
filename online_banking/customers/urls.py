from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('deposit/', views.deposit, name='deposit'),
    path('withdraw/', views.withdrawal, name='withdrawal'),
    path('transfer/', views.transfer, name='transfer'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('statement/<str:format_type>/', views.download_statement, name='download_statement'),
]