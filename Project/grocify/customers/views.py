from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import Customer

@login_required
def customers_dashboard(request):
    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(is_active=True).count()
    total_outstanding = Customer.objects.aggregate(
        Sum('outstanding_balance')
    )['outstanding_balance__sum'] or 0
    tier_count = Customer.objects.filter(tier__isnull=False).values('tier').distinct().count()
    recent_customers = Customer.objects.order_by('-joined_at')[:10]
    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'total_outstanding': total_outstanding,
        'tier_count': tier_count,
        'recent_customers': recent_customers,
    }
    return render(request, 'customers/dashboard.html', context)
