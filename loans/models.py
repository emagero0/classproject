from django.contrib.auth.models import AbstractUser
from django.db import models


# Extended User Model
class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    rating = models.FloatField(default=0.0)
    number_of_loans = models.PositiveIntegerField(default=0)  # Number of loans taken
    number_of_loans_repaid = models.PositiveIntegerField(default=0)  # Number of loans repaid

    def __str__(self):
        return self.username

    def update_rating(self):
        """Recalculate the rating based on reviews received."""
        reviews = self.reviews_received.all()
        if reviews:
            total_rating = sum([review.rating for review in reviews])
            self.rating = total_rating / len(reviews)
            self.save()


# Loan Status Enum
class LoanStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    COMPLETED = 'COMPLETED', 'Completed'


# Loan Application Model
class LoanApplication(models.Model):
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255)
    duration_in_months = models.PositiveIntegerField()
    collateral = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.PENDING
    )
    application_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def approve_application(self, lender):
        """Convert this LoanApplication into an actual Loan if approved."""
        if self.status != LoanStatus.PENDING:
            raise ValueError("This application has already been processed.")
        
        loan = Loan.objects.create(
            borrower=self.borrower,
            lender=lender,
            amount_requested=self.amount_requested,
            interest_rate=5.0,  # Example interest rate
            duration_in_months=self.duration_in_months,
            collateral=self.collateral,
            status=LoanStatus.APPROVED
        )
        self.status = LoanStatus.APPROVED
        self.save()  # Save the application as approved
        return loan

    def reject_application(self):
        """Reject the loan application."""
        self.status = LoanStatus.REJECTED
        self.save()

    def __str__(self):
        return f"Loan Application: {self.amount_requested} by {self.borrower.username}"


# Loan Model
class Loan(models.Model):
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowed_loans')
    lender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lent_loans')
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.FloatField()  # Percentage
    duration_in_months = models.PositiveIntegerField()
    collateral = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loan: {self.amount_requested} by {self.borrower.username}"

    def get_remaining_balance(self):
        """Calculate the remaining balance of the loan."""
        repayments = self.repayments.all()
        total_repaid = sum([repayment.amount_paid for repayment in repayments])
        return self.amount_requested + (self.amount_requested * self.interest_rate / 100) - total_repaid

    def is_completed(self):
        """Check if the loan is fully repaid."""
        return self.get_remaining_balance() <= 0


# Transaction Model
class Transaction(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE)
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions_as_lender')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions_as_borrower')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    is_repaid = models.BooleanField(default=False)

    def __str__(self):
        return f"Transaction: {self.amount} for {self.loan}"

    def repay(self, amount):
        """Repay a portion of the loan."""
        if self.loan.is_completed():
            raise ValueError("Loan is already fully repaid.")
        
        self.amount += amount
        self.is_repaid = self.loan.get_remaining_balance() - amount <= 0
        self.save()
        if self.is_repaid:
            self.loan.status = LoanStatus.COMPLETED
            self.loan.save()


# Review Model
class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveIntegerField()  # 1 to 5 stars
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review: {self.rating} for {self.reviewed_user.username}"