from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SaleTransaction
from inventory.models import InventoryItem, StockEntry, StockLedger

@receiver(post_save, sender=SaleTransaction)
def handle_sale_transaction(sender, instance, created, **kwargs):
    if not created:
        return

    # Deduct stock & log ledger
    for item in instance.items.all():
        product = item.product
        location = instance.location
        qty = item.quantity

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

    # Award loyalty points
    if instance.customer:
        cust = instance.customer
        cust.points += int(instance.total_amount)
        cust.save()
        cust.update_tier()