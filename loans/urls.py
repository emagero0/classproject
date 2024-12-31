# loans/urls.py
from django.urls import path
from loans import views
from django.contrib.auth import views as auth_views

app_name = 'loans'

urlpatterns = [
    path('', views.home, name='home'),  # Homepage of the 'loans' app
    path('apply/', views.loan_application_view, name='loan_application'),  # Loan application page
    path('list/', views.lender_dashboard, name='loan_list'),  # List all loans
    path('detail/<int:pk>/', views.loan_detail, name='loan_detail'),  # View details of a specific loan
    path('approve/<int:pk>/', views.approve_loan_view, name='approve_loan'),  # Approve or reject a loan
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('approve/<int:application_id>/', views.approve_loan_view, name='approve_loan'),
    path('transaction/<int:loan_id>/', views.transaction_view, name='transaction'),
     path('chat/<int:loan_id>/', views.chat_view, name='chat'),  # Chat page for specific loan
    path('review/<int:user_id>/', views.submit_review_view, name='submit_review'),
    path('register/', views.register_view, name='register'),
    path('lender-dashboard/', views.lender_dashboard, name='lender_dashboard'),
    path('borrower-dashboard/', views.borrower_dashboard, name='borrower_dashboard'),
]