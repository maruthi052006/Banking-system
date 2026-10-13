from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard-data/', views.dashboard_data, name='manager_dashboard_data'),
    path('officers/', views.officer_management, name='officer_management'),
    path('analytics/', views.branch_analytics, name='branch_analytics'),
    path('reports/', views.financial_reports, name='financial_reports'),
    path('large-transactions/', views.large_transactions, name='large_transactions'),
]