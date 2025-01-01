from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import LoanApplication, Loan, LoanStatus, Transaction
from .forms import UserRegistrationForm, EditProfileForm
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO

class LoanAppTests(TestCase):
    def setUp(self):
        """Setup method for creating initial data for the tests"""
        from .models import User
        self.client = Client()
        self.user = User.objects.create(username='testuser', password='testpassword')
        self.user.set_password('testpassword')
        self.user.save()
        self.admin_user = User.objects.create(username='adminuser', password='adminpassword', email='admin@test.com')
        self.admin_user.set_password('adminpassword')
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        self.loan_application = LoanApplication.objects.create(
            borrower=self.user,
            amount_requested=1000,
            purpose="Test Loan",
            duration_in_months=12,
            status = LoanStatus.PENDING
        )
        
        # Create completed loan applications for the borrower
        for i in range(3):
             loan_application = LoanApplication.objects.create(
                borrower=self.user,
                amount_requested=500,
                purpose="Test Loan",
                duration_in_months = 10,
                status = LoanStatus.COMPLETED,
             )
        
        # Create an approved loan application
        for i in range(1):
             loan_application2 = LoanApplication.objects.create(
            borrower=self.user,
             amount_requested=1000,
                purpose="Test Loan",
                 duration_in_months=12,
                 status = LoanStatus.APPROVED,
            )

    def test_home_page(self):
        """Test the home page loading"""
        response = self.client.get(reverse('loans:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loans/home.html')


    def test_loan_application_form_valid(self):
        """Test the loan application is valid"""
        self.client.force_login(self.user)
        url = reverse('loans:loan_application')
        data = {
            'amount_requested': 2000,
            'purpose': "Test Application",
            'duration_in_months': 20,
            'collateral': "My car"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) # or 302
        self.assertTemplateUsed(response, 'loans/loan_application.html')
        self.assertContains(response, 'Loan application submitted succesfully!')


    def test_loan_application_form_invalid(self):
        """Test the loan application is invalid"""
        self.client.force_login(self.user)
        url = reverse('loans:loan_application')
        data = {
            'amount_requested': 0,
            'purpose': "Test Application",
            'duration_in_months': 20,
             'collateral': "My car"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertContains(response, "Amount requested must be greater than zero.")

    def test_approve_loan_view_unauthorized(self):
        """Test unauthorized user cannot access approve loan page"""
        self.client.force_login(self.user)
        url = reverse('loans:approve_loan', kwargs={'application_id': self.loan_application.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_approve_loan_view_authorized(self):
        """Test authorized user can access approve loan page"""
        self.client.force_login(self.admin_user)
        url = reverse('loans:approve_loan', kwargs={'application_id': self.loan_application.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loans/approve_loan.html')

    def test_loan_approval_process_valid(self):
        """Test the loan approval process when a valid form is submitted"""
        self.client.force_login(self.admin_user)
        url = reverse('loans:approve_loan', kwargs={'application_id': self.loan_application.id})
        data = {
            'borrower': self.user.id,
            'lender': self.admin_user.id,
            'amount_requested': 1000,
            'interest_rate': 5.0,
            'duration_in_months': 12,
            'collateral': "car",
            'status': LoanStatus.APPROVED
        }
        response = self.client.post(url, data)
        loan = Loan.objects.filter(borrower=self.user).first()
        self.assertRedirects(response, reverse('loans:loan_detail', kwargs={'pk':loan.id}))
        self.assertEqual(loan.status, LoanStatus.APPROVED)
        loan_app = LoanApplication.objects.filter(borrower=self.user, status=LoanStatus.APPROVED).first()
        self.assertEqual(loan_app.status, LoanStatus.APPROVED)

    def test_loan_approval_process_invalid(self):
        """Test the loan approval process when a invalid form is submitted"""
        self.client.force_login(self.admin_user)
        url = reverse('loans:approve_loan', kwargs={'application_id': self.loan_application.id})
        data = {
            'borrower': self.user.id,
            'lender': self.admin_user.id,
            'amount_requested': 0,
            'interest_rate': 5.0,
            'duration_in_months': 12,
            'collateral': "car",
            'status': LoanStatus.APPROVED
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())

    def test_register_view_valid_form(self):
        """Test register view when the form submitted is valid"""
        from .models import User # import the user model from the app
        url = reverse('loans:register')
        data = {
        'username': 'testuser2',
        'email': 'test2@test.com',
        'password': 'Testpassword1!',
        'password_confirmation': 'Testpassword1!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) #redirect after successfull login
        self.assertTrue(User.objects.filter(username='testuser2').exists())

    def test_register_view_invalid_form(self):
        """Test register view when the form submitted is invalid"""
        url = reverse('loans:register')
        data = {
             'username': 'testuser2',
             'email': 'test2@test.com',
             'password': 'Testpassword', #password does not have a digit
             'password_confirmation': 'Testpassword',
         }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) #not redirect
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertContains(response, "Password must contain at least one digit.")

    def test_login_view_valid(self):
        """Test Login View with a valid form"""
        url = reverse('loans:login')
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) #redirect

    def test_login_view_invalid(self):
        """Test Login View with invalid credentials"""
        url = reverse('loans:login')
        data = {'username': 'invaliduser', 'password': 'invalidpassword'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) #does not redirect
        form = response.context['form']
        self.assertFalse(form.is_valid())

    def test_logout_view(self):
        """Test logout view and verify redirect to the home page"""
        self.client.force_login(self.user)
        url = reverse('loans:logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('loans:home'))

    def test_edit_profile_view_valid_form(self):
        """Test the edit profile view with a valid form"""
        self.client.force_login(self.user)
        url = reverse('loans:edit_profile')
        image_data = BytesIO(b"some content for image")
        image_file = SimpleUploadedFile("test_image.jpg", image_data.read(), content_type="image/jpeg")
        data = {
            'profile_picture': image_file,
            'phone_number': '123-456-7890',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('loans:home'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '123-456-7890')
        self.assertIsNotNone(self.user.profile_picture)
    
    def test_edit_profile_view_invalid_form(self):
        """Test the edit profile view with an invalid form"""
        self.client.force_login(self.user)
        url = reverse('loans:edit_profile')
        data = {
            'phone_number': 'invalidnumber',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertContains(response, "Enter a valid phone number")