from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import login as auth_login, authenticate, logout
from .models import LoanApplication, Loan, Transaction, Review, LoanStatus, User
from .forms import LoanApplicationForm, LoanForm, TransactionForm, ReviewForm, UserRegistrationForm, EditProfileForm, LoanStatusUpdateForm
from django.contrib.auth.forms import AuthenticationForm


# View for Loan Application
def loan_application_view(request):
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            loan_application = form.save(commit=False)
            loan_application.borrower = request.user  # Set the current logged-in user as the borrower
            loan_application.save()
            return render(request, 'loans/loan_application.html', {'form': form, 'message':'Loan application submitted succesfully!'})  # Redirect to a success page
    else:
        form = LoanApplicationForm()
    return render(request, 'loans/loan_application.html', {'form': form})


# Business Logic for Loan Approval (with eligibility checks)
@login_required
def approve_loan_view(request, application_id):
    application = get_object_or_404(LoanApplication, id=application_id)

    # Ensure only admins can approve loans
    if not request.user.is_staff:
        return HttpResponse("You are not authorized to approve loans.", status=403)

    # Check if loan has already been processed
    if application.status != LoanStatus.PENDING:
        return HttpResponse("This loan has already been processed.", status=400)

    # Eligibility checks for loan approval
    if application.borrower.loan_applications.filter(status=LoanStatus.APPROVED).count() > 5:  # Borrower exceeds max loans
        return HttpResponse("The borrower has too many loans and is not eligible for this loan.", status=400)

    if application.borrower.loan_applications.filter(status=LoanStatus.REPAID).count() < 3:  # Borrower hasn't repaid enough loans
        return HttpResponse("The borrower hasn't repaid enough loans to qualify for this loan.", status=400)

    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            # Proceed with loan approval
            loan = form.save(commit=False)
            loan.borrower = application.borrower  # Set borrower to the application borrower
            loan.lender = request.user #set the current user as the lender
            loan.status = LoanStatus.APPROVED  # Approve the loan
            loan.save()

            # Update the LoanApplication status to reflect the approval
            application.status = LoanStatus.APPROVED
            application.save()

            return redirect('loans:loan_detail', pk=loan.id)
    else:
        form = LoanForm(initial={'borrower': application.borrower, 'lender':request.user, 'status': LoanStatus.APPROVED })  # Render the loan form for approval
    return render(request, 'loans/approve_loan.html', {'form': form, 'application': application})


# View for Transaction (payment/repayment)
def transaction_view(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    try:
        if request.method == 'POST':
            form = TransactionForm(request.POST)
            if form.is_valid():
                transaction = form.save(commit=False)
                transaction.loan = loan  # Attach the transaction to the loan
                transaction.lender = request.user
                transaction.borrower = loan.borrower
                transaction.save()
                return render(request, 'loans/transaction.html', {'form': form, 'loan': loan, 'message':'Transaction submitted successfully!'})
        else:
            form = TransactionForm(initial={'loan': loan})
        return render(request, 'loans/transaction.html', {'form': form, 'loan': loan})
    except ValueError as ve:
            return HttpResponse(f"Value Error : {ve}", status=400)

    except Exception as e:
            return HttpResponse(f"An error occurred: {e}", status=500)

def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    if request.method == 'POST':
        form = LoanStatusUpdateForm(request.POST)
        if form.is_valid():
            loan.status = form.cleaned_data['status']
            loan.save()
            return redirect('loans:loan_detail', pk=pk)
    else:
        form = LoanStatusUpdateForm(initial={'status':loan.status})
    return render(request, 'loans/loan_detail.html', {'loan': loan, 'form':form})


# View for Review submission
def submit_review_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()  # Save the review
            return redirect('loans:home')
    else:
        form = ReviewForm(initial={'reviewer': request.user.id})  # Set the current user as reviewer
    return render(request, 'loans/submit_review.html', {'form': form, 'reviewed_user':user})


# User Registration View
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            role = 'Borrower' #Default role is borrower
            try:
                group = Group.objects.get(name=role)
                user.groups.add(group)
            except Group.DoesNotExist:
                return HttpResponse("Invalid role selected.", status=400)
            auth_login(request, user)  # Log the user in immediately after registration
            return redirect('loans:home')  # Redirect to the home page or dashboard
    else:
        form = UserRegistrationForm()
    return render(request, 'registrations/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('loans:home')  # Redirect to home after login
    else:
         form = AuthenticationForm()
    return render(request, 'registrations/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('loans:home')

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('loans:home')  # Redirect to the home page after editing
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'loans/edit_profile.html', {'form': form})


# Role Checks
def is_lender(user):
    return user.groups.filter(name='Lender').exists()


def is_borrower(user):
    return user.groups.filter(name='Borrower').exists()


@login_required
@user_passes_test(is_lender)
def lender_dashboard(request):
    # Logic for lender dashboard
    loans = Loan.objects.filter(status=LoanStatus.PENDING)
    lender_transactions = Transaction.objects.filter(lender=request.user)
    return render(request, 'loans/lender_dashboard.html', {'loans': loans,  'lender_transactions':lender_transactions})


@login_required
@user_passes_test(is_borrower)
def borrower_dashboard(request):
    # Logic for borrower dashboard
    loan_applications = LoanApplication.objects.filter(borrower=request.user)
    borrowed_loans = Loan.objects.filter(borrower=request.user)
    borrower_transactions = Transaction.objects.filter(borrower=request.user)
    return render(request, 'loans/borrower_dashboard.html', {'loan_applications': loan_applications, 'borrowed_loans': borrowed_loans, 'borrower_transactions': borrower_transactions})


# Home View
def home(request):
    loans = Loan.objects.filter(status=LoanStatus.PENDING)
    users = User.objects.all()
    is_lender_user = is_lender(request.user)
    is_borrower_user = is_borrower(request.user)
    return render(request, 'loans/home.html', {'users':users, 'is_lender': is_lender_user, 'is_borrower': is_borrower_user, 'loans':loans})