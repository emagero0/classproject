from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, authenticate, logout
from .models import LoanApplication, Loan, Transaction, Review, LoanStatus, User, ChatMessage
from .forms import ApplicationForm, LoanForm, TransactionForm, ReviewForm, UserRegistrationForm, EditProfileForm, LoanStatusUpdateForm
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum


# View for Loan Application
@login_required
def loan_application_view(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            loan_application = form.save(commit=False)
            loan_application.borrower = request.user  # Set the current logged-in user as the borrower
            loan_application.save()
            return redirect('loans:home')
        else:
            return render(request, 'loans/loan_application.html', {'form':form})
    else:
        form = ApplicationForm()
    return render(request, 'loans/loan_application.html', {'form': form})


# Business Logic for Loan Approval (with eligibility checks)
@login_required
def approve_loan_view(request, application_id):
    application = get_object_or_404(LoanApplication, id=application_id)
    

    # Check if loan has already been processed 
    if application.status != LoanStatus.PENDING:
        return render(request, 'loans/approve_loan.html', {'message':"This loan has already been processed."}, status=400)

     #Eligibility checks - auth permission are tested via those types by object / data using framework test

    if application.borrower.loan_applications.filter(status=LoanStatus.APPROVED).count() > 5: # if check is bypassed via authentication state check it should implicitly work now. Valid objects validation

         return HttpResponse("The borrower has too many loans and is not eligible for this loan.", status=403)

    if application.borrower.loan_applications.filter(status=LoanStatus.COMPLETED).count() < 3: # implicit objects types validations. auth test implicitly makes valid object based states now via permission for this part

          return HttpResponse("The borrower hasn't repaid enough loans to qualify for this loan.", status=403)


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

            return redirect('loans:loan_detail', pk=loan.id) # post triggers the redirect, object setup from django implicitly does valid redirect or render correctly based on object authentication states created by implicit check


    else:
          form = LoanForm(initial={'borrower': application.borrower, 'lender':request.user, 'status': LoanStatus.APPROVED })  # Render the loan form for approval
   # test state django objects based testing validates if all checks for those sessions exist and view objects render correctly

    return render(request, 'loans/approve_loan.html', {'form': form, 'application': application},status=200)  #must do the render to explicitly set a return with all type setup to prevent  extra auth redirects of previous  view object (test validates with all implicit assumptions solved). Valid login session should make this a page state + http as intended. Django performs authorization + authentication with test session

# View for Transaction (payment/repayment)
@login_required
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

@login_required
def loan_detail(request, pk):
    try:
         loan = get_object_or_404(Loan, pk=pk)
    except:
          loan = get_object_or_404(LoanApplication, pk=pk)
          try:
              loan = get_object_or_404(Loan, borrower=loan.borrower, amount_requested=loan.amount_requested, duration_in_months=loan.duration_in_months, collateral=loan.collateral)
          except:
              pass
    if request.method == 'POST':
         form = LoanStatusUpdateForm(request.POST)
         if form.is_valid():
             loan.status = form.cleaned_data['status']
             loan.save()
             return redirect('loans:loan_detail', pk=pk)
    else:
         form = LoanStatusUpdateForm(initial={'status':loan.status})
    return render(request, 'loans/loan_detail.html', {'loan': loan, 'form':form})

@login_required
def loan_detail_json(request, loan_id):
    loan_application = get_object_or_404(LoanApplication, pk=loan_id)
    borrower = loan_application.borrower
    try:
          loan = get_object_or_404(Loan, borrower=borrower, amount_requested=loan_application.amount_requested, duration_in_months=loan_application.duration_in_months, collateral=loan_application.collateral)
          data = {
            'id': loan_application.id,
            'loan_id': loan.id,
            'borrower': {
                'username': borrower.username,
                'phone_number': borrower.phone_number,
            },
            'amount_requested': str(loan_application.amount_requested),
            'purpose': loan_application.purpose,
            'collateral': loan_application.collateral,
            'status': loan_application.status,
        }
    except:
        data = {
            'id': loan_application.id,
            'borrower': {
                'username': borrower.username,
                'phone_number': borrower.phone_number,
            },
            'amount_requested': str(loan_application.amount_requested),
            'purpose': loan_application.purpose,
            'collateral': loan_application.collateral,
            'status': loan_application.status,
        }
    return JsonResponse(data)


# View for Review submission
@login_required
def submit_review_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()  # Save the review
            return redirect('loans:home')
    else:
        form = ReviewForm(initial={'reviewer': request.user.id, 'reviewed_user': user.id})  # Set the current user as reviewer
    return render(request, 'loans/submit_review.html', {'form': form, 'reviewed_user':user})


# User Registration View
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            auth_login(request, user)  # Log the user in immediately after registration
            return redirect('loans:home')  # Redirect to the home page or dashboard
    else:
        form = UserRegistrationForm()
    return render(request, 'loans/registrations/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('loans:home')  # Redirect to home after login
    else:
         form = AuthenticationForm()
    next_url = request.META.get('HTTP_REFERER')
    return render(request, 'loans/registrations/login.html', {'form': form, 'next':next_url})

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
            return render(request, 'loans/edit_profile.html', {'form': form})
    form = EditProfileForm(instance=request.user)
    return render(request, 'loans/edit_profile.html', {'form': form})


@login_required
def loan_list(request):
    # Logic for lender dashboard
    loans = Loan.objects.all()
    lender_transactions = Transaction.objects.filter(lender=request.user)
    return render(request, 'loans/loan_list.html', {'loans': loans,  'lender_transactions':lender_transactions})


@login_required
def borrower_dashboard(request):
    # Logic for borrower dashboard
    loan_applications = LoanApplication.objects.filter(borrower=request.user)
    borrowed_loans = Loan.objects.filter(borrower=request.user)
    borrower_transactions = Transaction.objects.filter(borrower=request.user)
    return render(request, 'loans/borrower_dashboard.html', {'loan_applications': loan_applications, 'borrowed_loans': borrowed_loans, 'borrower_transactions': borrower_transactions})


# Home View
def home(request):
    loan_applications = LoanApplication.objects.filter(status=LoanStatus.PENDING)
    if request.user.is_authenticated:
         # Borrower Dashboard data
        borrower_applications = LoanApplication.objects.filter(borrower=request.user)
        borrowed_loans = Loan.objects.filter(borrower=request.user, status=LoanStatus.APPROVED)
        approved_loan_applications = LoanApplication.objects.filter(borrower=request.user, status=LoanStatus.APPROVED)
        total_amount_owed = Loan.objects.filter(borrower=request.user, status=LoanStatus.APPROVED).aggregate(total=Sum('amount_requested'))['total'] or 0

         #Lender Dashboard Data
        active_loans = Loan.objects.filter(lender=request.user, status=LoanStatus.APPROVED)
        total_lent_amount = Loan.objects.filter(lender=request.user, status=LoanStatus.APPROVED).aggregate(total=Sum('amount_requested'))['total'] or 0

        recent_transactions = (Transaction.objects.filter(borrower=request.user).order_by('-transaction_date')[:5] | Transaction.objects.filter(lender=request.user).order_by('-transaction_date')[:5]).distinct()
        recent_messages = ChatMessage.objects.filter(receiver=request.user).order_by('-timestamp')[:5]

        return render(request, 'loans/home.html', {
                'loans': loan_applications,
                'loan_applications': borrower_applications,
                'approved_loan_applications': approved_loan_applications,
                'borrowed_loans': borrowed_loans,
                'total_amount_owed': total_amount_owed,
               'active_loans': active_loans,
                'total_lent_amount': total_lent_amount,
                'recent_transactions': recent_transactions,
                 'recent_messages': recent_messages,
           })
    else:
        return render(request, 'loans/home.html', {'loans': loan_applications})
    return render(request, 'loans/home.html', {'loans': loan_applications})

@login_required
def chat_view(request, loan_id):
    try:
         loan = get_object_or_404(Loan, pk=loan_id)
    except:
          loan_application = get_object_or_404(LoanApplication, pk=loan_id)
          loan = get_object_or_404(Loan, borrower=loan_application.borrower, amount_requested=loan_application.amount_requested, duration_in_months=loan_application.duration_in_months, collateral=loan_application.collateral)
    messages = ChatMessage.objects.filter(loan=loan).order_by('timestamp')

    if request.method == "POST":
        message = request.POST.get('message')
        ChatMessage.objects.create(
            loan = loan,
            sender=request.user,
            receiver=loan.lender if request.user == loan.borrower else loan.borrower,
            message=message,
        )
        return redirect('loans:chat', loan_id=loan.id)
    return render(request, 'loans/chat.html', {
        'loan': loan,
        'messages': messages,
    })