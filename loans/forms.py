# loans/forms.py

from django import forms
from .models import LoanApplication, Loan, Transaction, Review, User, LoanStatus
from django.contrib.auth.models import Group

# Form for LoanApplication
class ApplicationForm(forms.ModelForm):
    amount_requested = forms.CharField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    duration_in_months = forms.CharField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    class Meta:
        model = LoanApplication
        fields = ['amount_requested', 'purpose', 'duration_in_months', 'collateral']
        widgets = {
            
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
          
            'collateral': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_amount_requested(self):
        amount = self.cleaned_data.get('amount_requested')
        try:
            amount = int(amount)
        except ValueError:
            raise forms.ValidationError("Amount requested must be a number")
        if amount <= 0:
            raise forms.ValidationError("Amount requested must be greater than zero.")
        return amount

    def clean_duration_in_months(self):
        duration = self.cleaned_data.get('duration_in_months')
        try:
            duration = int(duration)
        except ValueError:
            raise forms.ValidationError("Duration must be a number.")
        if duration <= 0:
            raise forms.ValidationError("Duration must be greater than zero.")
        return duration
    
# Form for Loan (Used for approving a loan application)
class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['borrower', 'lender', 'amount_requested', 'interest_rate', 'duration_in_months', 'collateral', 'status']
        widgets = {
            'borrower': forms.Select(attrs={'class': 'form-control', 'style':'display:none'}),
             'lender': forms.Select(attrs={'class': 'form-control', 'style':'display:none'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_in_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'collateral': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control', 'style':'display:none'}),
        }

# Form for Transaction (To handle payments or repayments)
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['loan', 'amount', 'is_repaid']
        widgets = {
            'loan': forms.Select(attrs={'class': 'form-control', 'style':'display:none'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_repaid': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style':'display:none'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Transaction amount must be greater than zero.")
        return amount

# Form for Review
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['reviewer', 'reviewed_user', 'rating', 'comment']
        widgets = {
            'reviewer': forms.HiddenInput(),  # Hidden field for logged-in user
            'reviewed_user': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'minlength': 8}))
    password_confirmation = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'minlength': 8}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_password(self):
       password = self.cleaned_data.get('password')
       if not any(char.isdigit() for char in password):
          raise forms.ValidationError("Password must contain at least one digit.")
       if not any(not char.isalnum() for char in password):
          raise forms.ValidationError("Password must contain at least one special character.")
       return password

    def clean_password_confirmation(self):
        password = self.cleaned_data.get('password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if password != password_confirmation:
            raise forms.ValidationError("Passwords do not match.")
        return password_confirmation


# Form for Editing User Profile
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture', 'phone_number']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

#Form for updating loan status
class LoanStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=LoanStatus.choices, widget=forms.Select(attrs={'class':'form-control'}))

#Form for displaying profile
class ProfileForm(forms.Form):
  pass