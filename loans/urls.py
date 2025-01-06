# loans/urls.py
from django.urls import path
from loans import views
from django.contrib.auth import views as auth_views

app_name = 'loans'

urlpatterns = [
    path('', views.home, name='home'),  # Homepage of the 'loans' app
    path('apply/', views.loan_application_view, name='loan_application'),  # Loan application page
    path('list/', views.loan_list, name='loan_list'),  # List all loans
    path('loan/detail/<int:pk>/', views.loan_detail, name='loan_detail'),  # View details of a specific loan
    path('application/detail/<int:pk>/', views.loan_detail, name='application_detail'), #View details of a loan applicaation
    path('approve/<int:application_id>/', views.approve_loan_view, name='approve_loan'), # Approve or reject a loan
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('transaction/<int:loan_id>/', views.transaction_view, name='transaction'),
    path('chat/<int:loan_id>/', views.chat_view, name='chat'),  # Chat page for specific loan
    path('loan-details/<int:loan_id>/', views.loan_detail_json, name='loan_detail_json'),
    path('review/<int:user_id>/', views.submit_review_view, name='submit_review'),
    path('register/', views.register_view, name='register'),
    path('borrower-dashboard/', views.borrower_dashboard, name='borrower_dashboard'),
    path('profile/', views.profile_view, name='profile'), # User Profile page
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
]