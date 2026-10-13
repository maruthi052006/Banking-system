from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.officer_dashboard, name='officer_dashboard'),
    path('dashboard-data/', views.dashboard_data, name='officer_dashboard_data'),
    path('customers/', views.customer_management, name='customer_management'),
    path('account-approvals/', views.account_approvals, name='account_approvals'),
    path('transactions/', views.transaction_monitoring, name='transaction_monitoring'),
    path('transactions/<uuid:transaction_id>/review/', views.review_transaction, name='review_transaction'),
    path('send-notification/', views.send_notification, name='send_notification'),
]