from django.contrib import admin
from .models import User, LoanApplication, Loan, Transaction, Review

# Inline model for Review under User
class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1
    fk_name = 'reviewed_user'  # Use 'reviewed_user' ForeignKey for the inline

# Custom admin class for User model
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'rating', 'number_of_loans', 'number_of_loans_repaid')
    search_fields = ('username', 'email', 'phone_number')
    list_filter = ('rating', 'number_of_loans', 'number_of_loans_repaid')
    ordering = ('username',)  # Order by username by default
    inlines = [ReviewInline]  # Show related reviews inline under User

# Inline model for Transaction under Loan
class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 1  # Number of empty forms to display initially

# Custom admin class for LoanApplication model
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'amount_requested', 'purpose', 'status', 'application_date', 'updated_at')
    search_fields = ('borrower__username', 'amount_requested', 'purpose')
    list_filter = ('status', 'application_date', 'updated_at')
    ordering = ('-application_date',)  # Order by application date (newest first)

# Custom admin class for Loan model
class LoanAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'lender', 'amount_requested', 'status', 'created_at', 'updated_at')
    search_fields = ('borrower__username', 'lender__username', 'amount_requested')
    list_filter = ('status', 'lender')
    ordering = ('-created_at',)  # Order by creation date (newest first)
    inlines = [TransactionInline]  # Show related transactions inline

# Custom admin class for Transaction model
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('loan', 'lender', 'borrower', 'amount', 'transaction_date', 'is_repaid')
    search_fields = ('loan__borrower__username', 'loan__lender__username', 'amount')
    list_filter = ('is_repaid', 'transaction_date')
    ordering = ('-transaction_date',)  # Order by transaction date (newest first)

# Custom admin class for Review model
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewed_user', 'rating', 'created_at')
    search_fields = ('reviewer__username', 'reviewed_user__username', 'rating')
    list_filter = ('rating', 'created_at')
    ordering = ('-created_at',)  # Order by review creation date (newest first)

# Registering models with custom admin classes
admin.site.register(User, UserAdmin)
admin.site.register(LoanApplication, LoanApplicationAdmin)
admin.site.register(Loan, LoanAdmin)  # Register Loan model with custom admin
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Review, ReviewAdmin)
