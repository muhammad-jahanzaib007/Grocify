from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import LoyaltyProfile, Reward
from customers.models import Customer

# ─── DASHBOARD VIEW ──────────────────────────────────────────────────────
@login_required
def loyalty_dashboard(request):
    profiles = LoyaltyProfile.objects.select_related('customer', 'tier').all()
    return render(request, 'loyalty/dashboard.html', {'profiles': profiles})


# ─── POINT HISTORY VIEW ──────────────────────────────────────────────────
@login_required
def transaction_history(request):
    customer_id = request.GET.get('customer_id')
    customer = get_object_or_404(Customer, id=customer_id) if customer_id else Customer.get_walkin_customer()
    profile, _ = LoyaltyProfile.objects.get_or_create(customer=customer)
    transactions = profile.transactions.all().order_by('-date')
    return render(request, 'loyalty/history.html', {'profile': profile, 'transactions': transactions})


# ─── REWARD REDEMPTION VIEW ──────────────────────────────────────────────
@login_required
def redeem_reward(request):
    rewards = Reward.objects.filter(is_active=True).order_by('points_required')
    return render(request, 'loyalty/redeem.html', {'rewards': rewards})