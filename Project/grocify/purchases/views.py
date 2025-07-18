from django.shortcuts import render
from django.db import transaction
from django.views import generic
from django.urls import reverse_lazy
from .models import PurchaseOrder, PurchaseItem, PurchaseReceipt

# Create your views here.

def purchase_orders_dashboard(request):
    """
    Render the purchase orders dashboard page.
    """
    # Query purchase order data and pass to template
    orders = PurchaseOrder.objects.all()
    context = {
        'page_title': 'Purchases Dashboard',
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='Pending').count(),
        'received_orders': orders.filter(status='Received').count(),
        'cancelled_orders': orders.filter(status='Cancelled').count(),
        'recent_orders': orders.order_by('-date_ordered')[:10],
    }
    return render(request, 'purchases/dashboard.html', context)

class PurchaseOrderListView(generic.ListView):
    model = PurchaseOrder
    template_name = 'purchases/order_list.html'
    context_object_name = 'purchase_orders'

class PurchaseOrderDetailView(generic.DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    context_object_name = 'purchase_order'

from .forms import PurchaseItemFormSet

class PurchaseOrderCreateView(generic.CreateView):
    model = PurchaseOrder
    fields = ['supplier', 'location', 'date_ordered', 'status', 'notes']
    template_name = 'purchases/order_form.html'
    success_url = reverse_lazy('purchases:order_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = PurchaseItemFormSet(self.request.POST)
        else:
            data['items'] = PurchaseItemFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super().form_valid(form)

class PurchaseOrderUpdateView(generic.UpdateView):
    model = PurchaseOrder
    fields = ['supplier', 'location', 'date_ordered', 'status', 'notes']
    template_name = 'purchases/order_form.html'
    success_url = reverse_lazy('purchases:order_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = PurchaseItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = PurchaseItemFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super().form_valid(form)

class PurchaseOrderDeleteView(generic.DeleteView):
    model = PurchaseOrder
    template_name = 'purchases/order_confirm_delete.html'
    success_url = reverse_lazy('purchases:order_list')

class PurchaseItemCreateView(generic.CreateView):
    model = PurchaseItem
    fields = ['purchase_order', 'product', 'quantity', 'cost_price']
    template_name = 'purchases/item_form.html'

    def get_success_url(self):
        return reverse_lazy('purchases:order_detail', kwargs={'pk': self.object.purchase_order.pk})

class PurchaseReceiptCreateView(generic.CreateView):
    model = PurchaseReceipt
    fields = ['purchase_order', 'notes']
    template_name = 'purchases/receipt_form.html'

    def get_initial(self):
        initial = super().get_initial()
        po_id = self.request.GET.get('purchase_order')
        if po_id:
            initial['purchase_order'] = po_id
        # Pre-fill received_by with current user
        initial['received_by'] = self.request.user.pk
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        po_id = self.request.GET.get('purchase_order')
        if po_id:
            try:
                context['purchase_order'] = PurchaseOrder.objects.get(pk=po_id)
            except PurchaseOrder.DoesNotExist:
                context['purchase_order'] = None
        return context

    def form_valid(self, form):
        form.instance.received_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('purchases:receipt_detail', kwargs={'pk': self.object.pk})

class PurchaseReceiptDetailView(generic.DetailView):
    model = PurchaseReceipt
    template_name = 'purchases/receipt_detail.html'
    context_object_name = 'purchase_receipt'
