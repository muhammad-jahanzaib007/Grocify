from django.shortcuts import render
from django.db import transaction
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PurchaseOrder, PurchaseItem, PurchaseReceipt
from inventory.models import Location
from sales.views import get_selected_location
from .forms import PurchaseItemFormSet


@login_required
def purchase_orders_dashboard(request):
    loc = get_selected_location(request)
    print(f"DEBUG: Selected location from session: {loc}")
    print(f"DEBUG: Session data: {dict(request.session)}")
    
    orders = PurchaseOrder.objects.select_related('supplier', 'location').all()
    print(f"DEBUG: Total orders before filtering: {orders.count()}")
    
    if loc:
        orders = orders.filter(location_id=loc)
        print(f"DEBUG: Orders after filtering by location {loc}: {orders.count()}")
    else:
        print("DEBUG: No location filter applied - showing all orders")

    # Safe location retrieval with error handling
    current_location = None
    if loc:
        try:
            current_location = Location.objects.get(id=loc)
        except Location.DoesNotExist:
            current_location = None

    context = {
        'page_title': 'Purchases Dashboard',
        'current_location': current_location,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='Pending').count(),
        'received_orders': orders.filter(status='Received').count(),
        'cancelled_orders': orders.filter(status='Cancelled').count(),
        'recent_orders': orders.select_related('supplier', 'location').order_by('-date_ordered')[:10],
    }
    return render(request, 'purchases/dashboard.html', context)


class PurchaseOrderListView(LoginRequiredMixin, generic.ListView):
    model = PurchaseOrder
    template_name = 'purchases/order_list.html'
    context_object_name = 'purchase_orders'
    def get_queryset(self):
        qs = super().get_queryset().select_related('supplier', 'location')
        loc = get_selected_location(self.request)
        return qs.filter(location_id=loc) if loc else qs


class PurchaseOrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    context_object_name = 'purchase_order'
    def get_initial(self):
        initial = super().get_initial()
        loc = get_selected_location(self.request)
        if loc:
            initial['location'] = loc
        return initial


class PurchaseOrderCreateView(LoginRequiredMixin, generic.CreateView):
    model = PurchaseOrder
    fields = ['supplier', 'location', 'date_ordered', 'status', 'notes']
    template_name = 'purchases/order_form.html'
    success_url = reverse_lazy('purchases:order_list')
    def get_initial(self):
        initial = super().get_initial()
        loc = get_selected_location(self.request)
        if loc:
            initial['location'] = loc
        return initial

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

class PurchaseOrderUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = PurchaseOrder
    fields = ['supplier', 'location', 'date_ordered', 'status', 'notes']
    template_name = 'purchases/order_form.html'
    success_url = reverse_lazy('purchases:order_list')
    def get_initial(self):
        initial = super().get_initial()
        loc = get_selected_location(self.request)
        if loc:
            initial['location'] = loc
        return initial

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

class PurchaseOrderDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = PurchaseOrder
    template_name = 'purchases/order_confirm_delete.html'
    success_url = reverse_lazy('purchases:order_list')

class PurchaseItemCreateView(LoginRequiredMixin, generic.CreateView):
    model = PurchaseItem
    fields = ['purchase_order', 'product', 'quantity', 'cost_price']
    template_name = 'purchases/item_form.html'

    def get_initial(self):
        initial = super().get_initial()
        po_id = self.request.GET.get('purchase_order')
        if po_id:
            initial['purchase_order'] = po_id
        return initial

    def get_success_url(self):
        return reverse_lazy('purchases:order_detail', kwargs={'pk': self.object.purchase_order.pk})

class PurchaseItemDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = PurchaseItem
    
    def get_success_url(self):
        return reverse_lazy('purchases:order_detail', kwargs={'pk': self.object.purchase_order.pk})
    
    def delete(self, request, *args, **kwargs):
        from django.http import JsonResponse
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Only allow deletion if order is still pending
        if self.object.purchase_order.status != 'Pending':
            return JsonResponse({'error': 'Cannot delete items from non-pending orders'}, status=400)
            
        self.object.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        else:
            return super().delete(request, *args, **kwargs)

class PurchaseReceiptCreateView(LoginRequiredMixin, generic.CreateView):
    model = PurchaseReceipt
    fields = ['purchase_order', 'notes']
    template_name = 'purchases/receipt_form.html'

    def get_initial(self):
        initial = super().get_initial()
        po_id = self.request.GET.get('purchase_order')
        if po_id:
            initial['purchase_order'] = po_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        po_id = self.request.GET.get('purchase_order')
        if po_id:
            try:
                purchase_order = PurchaseOrder.objects.prefetch_related('items__product').get(pk=po_id)
                context['purchase_order'] = purchase_order
                # Add formset for receipt items
                from .forms import PurchaseReceiptItemFormSet
                if self.request.POST:
                    context['receipt_items'] = PurchaseReceiptItemFormSet(self.request.POST)
                else:
                    # Pre-populate with purchase order items
                    context['receipt_items'] = PurchaseReceiptItemFormSet(
                        initial=[{
                            'purchase_item': item.id,
                            'quantity_received': item.quantity,  # Default to full quantity
                            'quantity_damaged': 0
                        } for item in purchase_order.items.all()]
                    )
            except (PurchaseOrder.DoesNotExist, ValueError):
                context['purchase_order'] = None
                context['receipt_items'] = None
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        receipt_items = context['receipt_items']
        
        with transaction.atomic():
            form.instance.received_by = self.request.user
            self.object = form.save()
            
            if receipt_items and receipt_items.is_valid():
                receipt_items.instance = self.object
                receipt_items.save()
                
                # Update inventory for each received item
                self._update_inventory(self.object)
                
                # Update purchase order status if all items received
                purchase_order = self.object.purchase_order
                total_ordered = sum(item.quantity for item in purchase_order.items.all())
                total_received = sum(item.quantity_received for item in self.object.items.all())
                
                if total_received >= total_ordered:
                    purchase_order.status = 'Received'
                    purchase_order.save()
                    
        return super().form_valid(form)
    
    def _update_inventory(self, receipt):
        """Update inventory levels when items are received"""
        from inventory.models import InventoryItem, StockEntry, StockLedger, DamageReport, AuditLog
        
        for receipt_item in receipt.items.all():
            product = receipt_item.purchase_item.product
            location = receipt.purchase_order.location
            good_quantity = receipt_item.quantity_received - receipt_item.quantity_damaged
            
            # Get or create inventory item for this product and location
            inventory_item, created = InventoryItem.objects.get_or_create(
                product=product,
                location=location,
                defaults={'qty_on_hand': 0}
            )
            
            # Record the stock movement for received items
            if receipt_item.quantity_received > 0:
                old_quantity = inventory_item.qty_on_hand
                inventory_item.qty_on_hand += good_quantity
                inventory_item.save()
                
                # Create stock entry for the received items
                stock_entry = StockEntry.objects.create(
                    product=product,
                    location=location,
                    quantity=good_quantity,
                    entry_type='purchase',
                    reference_number=f"PO-{receipt.purchase_order.id}-R{receipt.id}",
                    note=f"Received from Purchase Order #{receipt.purchase_order.id}",
                    created_by=receipt.received_by
                )
                
                # Create stock ledger entry
                StockLedger.objects.create(
                    product=product,
                    location=location,
                    quantity_before=old_quantity,
                    quantity_changed=good_quantity,
                    quantity_after=inventory_item.qty_on_hand,
                    related_entry=stock_entry
                )
                
                # Create audit log
                AuditLog.objects.create(
                    action_type='purchase_received',
                    user=receipt.received_by,
                    product=product,
                    location=location,
                    related_id=receipt.id,
                    note=f"Received {good_quantity} units from PO #{receipt.purchase_order.id}"
                )
            
            # Handle damaged items if any
            if receipt_item.quantity_damaged > 0:
                # Create damage report
                damage_value = receipt_item.quantity_damaged * receipt_item.purchase_item.cost_price
                DamageReport.objects.create(
                    product=product,
                    location=location,
                    damage_type='received_damaged',
                    quantity=receipt_item.quantity_damaged,
                    value_lost=damage_value,
                    description=f"Damaged items received in PO #{receipt.purchase_order.id}. {receipt_item.notes or 'No additional notes.'}",
                    reported_by=receipt.received_by,
                    related_purchase=receipt.purchase_order,
                    is_processed=True
                )
                
                # Create stock entry for damaged items (negative quantity)
                damage_entry = StockEntry.objects.create(
                    product=product,
                    location=location,
                    quantity=-receipt_item.quantity_damaged,
                    entry_type='damage',
                    reference_number=f"PO-{receipt.purchase_order.id}-R{receipt.id}-DMG",
                    note=f"Damaged items received from PO #{receipt.purchase_order.id}",
                    created_by=receipt.received_by
                )
                
                # Create audit log for damage
                AuditLog.objects.create(
                    action_type='damage_report',
                    user=receipt.received_by,
                    product=product,
                    location=location,
                    related_id=receipt.id,
                    note=f"Reported {receipt_item.quantity_damaged} damaged units from PO #{receipt.purchase_order.id}"
                )

    def get_success_url(self):
        return reverse_lazy('purchases:receipt_detail', kwargs={'pk': self.object.pk})

class PurchaseReceiptDetailView(LoginRequiredMixin, generic.DetailView):
    model = PurchaseReceipt
    template_name = 'purchases/receipt_detail.html'
    context_object_name = 'purchase_receipt'
