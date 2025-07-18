from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import DamageReportSnapshot
from sales.views import get_selected_location
from expenses.models import Expense
from purchases.models import PurchaseOrder

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

class DamageReportSnapshotListView(LoginRequiredMixin, ListView):
    model = DamageReportSnapshot
    template_name = 'reports/snapshot_list.html'
    context_object_name = 'snapshots'

class DamageReportSnapshotDetailView(LoginRequiredMixin, DetailView):
    model = DamageReportSnapshot
    template_name = 'reports/snapshot_detail.html'
    context_object_name = 'snapshot'

class DamageReportSnapshotCreateView(LoginRequiredMixin, CreateView):
    model = DamageReportSnapshot
    fields = ['product', 'location', 'damage_type', 'quantity', 'value_lost', 'reported_at', 'reported_by', 'related_purchase']
    template_name = 'reports/snapshot_form.html'
    success_url = reverse_lazy('reports:snapshot_list')

class DamageReportSnapshotUpdateView(LoginRequiredMixin, UpdateView):
    model = DamageReportSnapshot
    fields = ['product', 'location', 'damage_type', 'quantity', 'value_lost', 'reported_at', 'reported_by', 'related_purchase']
    template_name = 'reports/snapshot_form.html'
    success_url = reverse_lazy('reports:snapshot_list')

class DamageReportSnapshotDeleteView(LoginRequiredMixin, DeleteView):
    model = DamageReportSnapshot
    template_name = 'reports/snapshot_confirm_delete.html'
    success_url = reverse_lazy('reports:snapshot_list')
