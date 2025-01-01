from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model #updated
from loans.models import LoanApplication, LoanStatus
from loans.forms import LoanApplicationForm
from http import HTTPStatus

class LoanApplicationTest(TestCase):

    def setUp(self):
        # Create a test user
        User = get_user_model() #updated to use django get_user_model method
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')
        self.loan_application_url = reverse('loans:loan_application')
        self.home_url = reverse('loans:home')
    def test_loan_application_form_renders_correctly(self):
        response = self.client.get(self.loan_application_url)
        self.assertEqual(response.status_code, 200) #Ensure that url renders
        self.assertIsInstance(response.context['form'], LoanApplicationForm) #Checks if instance of right form type
    
    def test_loan_application_submission(self):
        data = {
            'amount_requested': 1000,
            'purpose': 'Test Purpose',
            'duration_in_months': 12,
            'collateral': 'Test Collateral',
        }
        response = self.client.post(self.loan_application_url, data)
        self.assertEqual(response.status_code, 302) # ensure that the page is redirected after form submission
        self.assertRedirects(response, self.home_url) #check if redirect is successful
        self.assertEqual(LoanApplication.objects.count(), 1) #check if application exists
        application = LoanApplication.objects.first()
        self.assertEqual(application.borrower, self.user) #check user is assigned to application
        self.assertEqual(application.amount_requested, data['amount_requested']) #check amount is recorded correctly
        self.assertEqual(application.status, LoanStatus.PENDING) #check if status is set to pending

    def test_loan_application_submission_invalid_amount(self):
        # Test negative loan amount
        invalid_data = {
            'amount_requested': -100,
            'purpose': 'Test Purpose',
            'duration_in_months': 12,
            'collateral': 'Test Collateral'
        }
        response = self.client.post(self.loan_application_url, invalid_data)
        self.assertEqual(response.status_code, 200) #Ensure that the invalid form renders again
         # Extract the form from the response context
        form = response.context['form']
        self.assertFormError(form, 'amount_requested', "Amount requested must be greater than zero.")
        self.assertEqual(LoanApplication.objects.count(), 0) # Ensure it was not created due to invalid data
        
        # Test zero loan amount
        invalid_data = {
            'amount_requested': 0,
            'purpose': 'Test Purpose',
            'duration_in_months': 12,
            'collateral': 'Test Collateral'
        }
        response = self.client.post(self.loan_application_url, invalid_data)
        self.assertEqual(response.status_code, 200) #Ensure that the invalid form renders again
         # Extract the form from the response context
        form = response.context['form']
        self.assertFormError(form, 'amount_requested', "Amount requested must be greater than zero.")
        self.assertEqual(LoanApplication.objects.count(), 0) # Ensure it was not created due to invalid data
    def test_loan_application_submission_invalid_duration(self):
        # Test negative duration
        invalid_data = {
            'amount_requested': 1000,
            'purpose': 'Test Purpose',
            'duration_in_months': -12,
            'collateral': 'Test Collateral'
        }
        response = self.client.post(self.loan_application_url, invalid_data)
        self.assertEqual(response.status_code, 200) #Ensure that the invalid form renders again
          # Extract the form from the response context
        form = response.context['form']
        self.assertFormError(form, 'duration_in_months', "Duration must be greater than zero.")
        self.assertEqual(LoanApplication.objects.count(), 0) # Ensure it was not created due to invalid data

        # Test zero duration
        invalid_data = {
           'amount_requested': 1000,
            'purpose': 'Test Purpose',
            'duration_in_months': 0,
            'collateral': 'Test Collateral'
        }
        response = self.client.post(self.loan_application_url, invalid_data)
        self.assertEqual(response.status_code, 200) #Ensure that the invalid form renders again
          # Extract the form from the response context
        form = response.context['form']
        self.assertFormError(form, 'duration_in_months', "Duration must be greater than zero.")
        self.assertEqual(LoanApplication.objects.count(), 0) # Ensure it was not created due to invalid data

    def test_unauthenticated_user_access_redirects_to_login(self):
        self.client.logout() # Logout the client
        response = self.client.get(self.loan_application_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND) # Redirects to login as is required in view
        self.assertIn(reverse('loans:login'), response.url)