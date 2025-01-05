# tests/test_p2p_lending.py
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from loans.models import LoanApplication, Loan, Transaction, LoanStatus
from django.contrib.auth.models import Group, Permission

User = get_user_model()


class P2PLendingTest(TestCase):

    def setUp(self):
        self.client = Client()
        # Create test users
        self.borrower = User.objects.create_user(username='borrower', password='testpassword')
        self.lender = User.objects.create_user(username='lender', password='testpassword')
        # Setup initial borrower conditions
        self._create_completed_loan_cycle()


    def _login_user(self, user):
        self.client.login(username=user.username, password='testpassword')

    def _create_completed_loan_cycle(self):
            # Helper method to create a completed loan cycle for the borrower
            
            # make loan application
            loan_app = LoanApplication.objects.create(
                borrower=self.borrower,
                amount_requested=500,
                purpose=f"Test Loan cycle",
                duration_in_months=3,
                collateral='None',
                status=LoanStatus.APPROVED
            )
            # lender approves the loan
            loan = Loan.objects.create(
                borrower=self.borrower,
                lender=self.lender,
                amount_requested=500,
                interest_rate=5.0,
                duration_in_months=3,
                collateral='None',
                status=LoanStatus.APPROVED
            )

            # borrower completes a transaction to repay the loan
            Transaction.objects.create(
                loan=loan,
                lender=self.lender,
                borrower=self.borrower,
                amount=500,
                is_repaid=True
            )
            loan.status = LoanStatus.COMPLETED
            loan.save()
            loan_app.status = LoanStatus.COMPLETED
            loan_app.save()


    def test_full_loan_cycle(self):
        # 1. Borrower Creates a Loan Application
        self._login_user(self.borrower)
        application_data = {
            'amount_requested': 1000,
            'purpose': 'Test loan',
            'duration_in_months': 6,
            'collateral': 'Some asset',
        }
        response = self.client.post(reverse('loans:loan_application'), application_data)
        self.assertEqual(response.status_code, 302)  # Check redirect to home

        # Check if the application is in pending list
        pending_application = LoanApplication.objects.filter(borrower=self.borrower, status=LoanStatus.PENDING).first()
        self.assertIsNotNone(pending_application)

        # 2. Lender Approves the Loan
        self._login_user(self.lender)

        # Get the loan application id. We are making an assumption here that only 1 loan is pending in the system
        # this will always be the last one that was created.
        loan_app = LoanApplication.objects.filter(borrower=self.borrower).latest('application_date')

        response = self.client.get(reverse('loans:approve_loan', kwargs={'application_id': loan_app.id}))
        self.assertEqual(response.status_code, 200)
        loan_data = {
            'borrower': self.borrower.id,
            'lender': self.lender.id,
            'amount_requested': 1000,
            'interest_rate': 5.0,
            'duration_in_months': 6,
            'collateral': 'Some asset',
            'status': 'APPROVED'
        }
        response = self.client.post(reverse('loans:approve_loan', kwargs={'application_id': loan_app.id}), loan_data)
        self.assertEqual(response.status_code, 302)

        # Check the loan status updated
        loan = Loan.objects.filter(borrower=self.borrower, lender=self.lender).first()
        self.assertEqual(loan.status, LoanStatus.APPROVED)

        # Check if loan is present in lender dashboard
        response = self.client.get(reverse('loans:loan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Loan ID: {loan.id}")
        self.assertContains(response, f"Borrower: {self.borrower.username}")
        self.assertContains(response, f"Status: {LoanStatus.APPROVED}")

        # 3. Borrower Repays the Loan
        self._login_user(self.borrower)

        transaction_data = {
            'loan': loan.id,
            'amount': loan.amount_requested,
            'is_repaid': True,
            'lender': self.lender.id,
            'borrower': self.borrower.id,
        }
        response = self.client.post(reverse('loans:transaction', kwargs={'loan_id': loan.id}), transaction_data)
        self.assertEqual(response.status_code, 200)

        # Check the loan status updated to completed and the remaining balance is 0
        updated_loan = Loan.objects.get(id=loan.id)
        self.assertEqual(updated_loan.status, LoanStatus.COMPLETED)
        self.assertLessEqual(updated_loan.get_remaining_balance(), 0)  # remaining balance is less than or equal to 0.

        # Verify the completed loan is on the borrower dashboard.
        response = self.client.get(reverse('loans:borrower_dashboard'))
        self.assertContains(response, f"Loan ID: {loan.id}")
        self.assertContains(response, f"Status: {LoanStatus.COMPLETED}")

        # Verify the completed loan does not appear on the loan list
        response = self.client.get(reverse('loans:loan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f"Loan ID: {loan.id}")

    def test_unauthenticated_access(self):
        # Try to access protected pages without login
        response = self.client.get(reverse('loans:loan_application'))
        self.assertEqual(response.status_code, 302)  # redirect to login
        self.assertIn(reverse('loans:login'), response.url)

    def test_invalid_borrower_action(self):
        # Test when a loan has been completed a borrower cannot make any further payment

        #borrower makes a loan application
        self._login_user(self.borrower)
        application_data = {
            'amount_requested': 1000,
            'purpose': 'Test loan',
            'duration_in_months': 6,
            'collateral': 'Some asset',
        }
        response = self.client.post(reverse('loans:loan_application'), application_data)
        self.assertEqual(response.status_code, 302)  # Check redirect to home

        # Get the loan application id. We are making an assumption here that only 1 loan is pending in the system
        # this will always be the last one that was created.
        loan_app = LoanApplication.objects.filter(borrower=self.borrower).latest('application_date')

        # lender approves the loan
        self._login_user(self.lender)
        response = self.client.get(reverse('loans:approve_loan', kwargs={'application_id': loan_app.id}))
        self.assertEqual(response.status_code, 200)
        loan_data = {
            'borrower': self.borrower.id,
            'lender': self.lender.id,
            'amount_requested': 1000,
            'interest_rate': 5.0,
            'duration_in_months': 6,
            'collateral': 'Some asset',
            'status': 'APPROVED'
        }
        response = self.client.post(reverse('loans:approve_loan', kwargs={'application_id': loan_app.id}), loan_data)
        self.assertEqual(response.status_code, 302)

        # Check the loan status updated
        loan = Loan.objects.filter(borrower=self.borrower, lender=self.lender).first()
        self.assertEqual(loan.status, LoanStatus.APPROVED)

        # borrower repays the loan
        self._login_user(self.borrower)

        transaction_data = {
            'loan': loan.id,
            'amount': loan.amount_requested,
            'is_repaid': True,
            'lender': self.lender.id,
            'borrower': self.borrower.id,
        }
        response = self.client.post(reverse('loans:transaction', kwargs={'loan_id': loan.id}), transaction_data)
        self.assertEqual(response.status_code, 200)

        # check status
        updated_loan = Loan.objects.get(id=loan.id)
        self.assertEqual(updated_loan.status, LoanStatus.COMPLETED)

        # try another payment which should raise error.
        response = self.client.post(reverse('loans:transaction', kwargs={'loan_id': loan.id}), transaction_data)
        self.assertContains(response, "Loan is already fully repaid.", status_code=400)