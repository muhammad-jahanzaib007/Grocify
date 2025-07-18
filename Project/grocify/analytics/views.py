from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count
from .models import DamageReportSnapshot
from sales.views import get_selected_location
from expenses.models import Expense
from purchases.models import PurchaseOrder



@login_required
def reports_dashboard(request):
    return render(request, 'reports/dashboard.html')
@login_required
def reports_dashboard(request):
    loc = get_selected_location(request)
    qs = DamageReportSnapshot.objects.all()
    if loc:
        qs = qs.filter(location_id=loc)

    damage_summary = qs.values('damage_type').annotate(
        total_lost=Sum('value_lost'),
        incidents=Count('id')
    )

    return render(request, 'reports/dashboard.html', {
        'damage_summary': damage_summary,
    })
@login_required
def expenses_dashboard(request):
    loc = get_selected_location(request)
    qs = Expense.objects.all()
    if loc:
        qs = qs.filter(location_id=loc)

    total_spent = qs.aggregate(total=Sum('amount'))['total'] or 0
    recent = qs.order_by('-date')[:25]

    return render(request, 'expenses/dashboard.html', {
        'recent_expenses': recent,
        'total_spent': total_spent,
    })
@login_required
def purchase_orders_dashboard(request):
    loc = get_selected_location(request)
    qs = PurchaseOrder.objects.select_related('supplier').all()
    if loc:
        qs = qs.filter(location_id=loc)

    pending = qs.filter(status='Pending').count()
    received = qs.filter(status='Received').count()

    return render(request, 'purchases/dashboard.html', {
        'orders': qs[:25],
        'pending': pending,
        'received': received,
    })


