from django.contrib import admin
from inventory.models import InventoryItem, StockEntry, StockLedger
from django.contrib.auth.models import User
from .models import (
    PurchaseOrder, PurchaseItem,
    PurchaseReceipt, PurchaseReceiptItem
)
from django.db import transaction




class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1

@admin.action(description="✅ Mark as Received + Update Stock & Ledger")
def mark_as_received(modeladmin, request, queryset):
    user = request.user
    with transaction.atomic():
        for po in queryset:
            if po.status == 'Received':
                continue

            for item in po.items.select_related('product'):
                product = item.product
                location = po.location
                quantity = item.quantity

                inventory, _ = InventoryItem.objects.get_or_create(
                    product=product,
                    location=location
                )

                quantity_before = inventory.qty_on_hand
                inventory.qty_on_hand += quantity
                inventory.save()

                # StockEntry
                entry = StockEntry.objects.create(
                    product=product,
                    location=location,
                    quantity=quantity,
                    entry_type='purchase',
                    note=f"PO#{po.id}",
                    created_by=user
                )

                # Ledger record
                StockLedger.objects.create(
                    product=product,
                    location=location,
                    quantity_before=quantity_before,
                    quantity_changed=quantity,
                    quantity_after=inventory.qty_on_hand,
                    related_entry=entry
                )

            po.status = 'Received'
            po.save()

        modeladmin.message_user(request, "✅ Purchase Orders marked as received and inventory updated.")

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'location', 'date_ordered', 'status')
    list_filter = ('status', 'supplier', 'location')
    search_fields = ('supplier__name', 'notes')
    list_editable = ('status',)
    inlines = [PurchaseItemInline]
    actions = [mark_as_received]
    date_hierarchy = 'date_ordered'


class PurchaseReceiptItemInline(admin.TabularInline):
    model = PurchaseReceiptItem
    extra = 0

@admin.register(PurchaseReceipt)
class PurchaseReceiptAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'received_by', 'received_at')
    list_filter = ('received_by',)
    search_fields = ('purchase_order__id', 'received_by__username')
    inlines = [PurchaseReceiptItemInline]
    readonly_fields = ('received_at',)
    date_hierarchy = 'received_at'

