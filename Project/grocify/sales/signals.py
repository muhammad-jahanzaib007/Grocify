from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SaleTransaction
from inventory.models import InventoryItem, StockEntry, StockLedger

@receiver(post_save, sender=SaleTransaction)
def handle_sale_transaction(sender, instance, created, **kwargs):
    if not created or instance.is_return:
        return  # Only deduct stock on original sales

    for item in instance.items.select_related('product').all():
        product = item.product
        location = instance.location
        qty = item.quantity

        if not product or not location or qty <= 0:
            continue  # Skip invalid entries

        inventory, _ = InventoryItem.objects.get_or_create(
            product=product,
            location=location
        )

        before = inventory.qty_on_hand
        inventory.qty_on_hand -= qty
        inventory.save()

        entry = StockEntry.objects.create(
            product=product,
            location=location,
            quantity=-qty,
            entry_type='sale',
            note=f"Invoice {instance.invoice_number}",
            created_by=instance.cashier
        )

        StockLedger.objects.create(
            product=product,
            location=location,
            quantity_before=before,
            quantity_changed=-qty,
            quantity_after=inventory.qty_on_hand,
            related_entry=entry
        )

    # Loyalty points now handled in transaction.save() — avoids duplicate rewards