from django.shortcuts import redirect

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.path.startswith('/lender/') and not request.user.groups.filter(name='Lender').exists():
                return redirect('unauthorized')  # Redirect unauthorized access
            if request.path.startswith('/borrower/') and not request.user.groups.filter(name='Borrower').exists():
                return redirect('unauthorized')
        return self.get_response(request)
