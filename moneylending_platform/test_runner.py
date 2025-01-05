# moneylending_platform/test_runner.py
from django.conf import settings
from django.test.runner import DiscoverRunner
from loans.models import LoanApplication, Loan, Transaction, Review, LoanStatus, ChatMessage


class CustomTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        result = super().setup_databases(**kwargs)
        #Add logic here to setup a shared test data as fixture.
        return result