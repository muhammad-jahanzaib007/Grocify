from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import LoyaltyProfile

@login_required
def loyalty_dashboard(request):
    profile = LoyaltyProfile.objects.get(customer=request.user.customer)
    return render(request, 'loyalty/dashboard.html', {'profile': profile})

@login_required
def transaction_history(request):
    customer = Customer.get_walkin_customer()  # or however you identify them
    profile = LoyaltyProfile.objects.get(customer=customer)

    transactions = profile.transactions.all().order_by('-date')
    return render(request, 'loyalty/history.html', {'transactions': transactions})

@login_required
def redeem_reward(request):
    # You'll wire this up with Reward form logic later
    return render(request, 'loyalty/redeem.html')
from customers.models import Customer, LoyaltyProfile

@login_required
def loyalty_dashboard(request):
    customer_id = request.GET.get('customer_id')
    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id)
    else:
        customer = Customer.get_walkin_customer()  # fallback

    profile = LoyaltyProfile.objects.get(customer=customer)
    return render(request, 'loyalty/dashboard.html', {'profile': profile})