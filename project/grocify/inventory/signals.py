from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from inventory.models import (
    DamageReport, InventoryItem, StockEntry,
    StockLedger, AuditLog
)
from analytics.models import DamageReportSnapshot
import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=DamageReport)
def handle_damage_report(sender, instance, created, **kwargs):
    if not created:
        return
    logger.warning("📣 DamageReport signal fired for ID: %s", instance.id)
    # Snapshot for analytics
    DamageReportSnapshot.objects.create(
        product=instance.product,
        location=instance.location,
        damage_type=instance.damage_type,
        quantity=instance.quantity,
        value_lost=instance.value_lost,
        reported_at=instance.reported_at,
        reported_by=instance.reported_by,
        related_purchase=instance.related_purchase
    )

    try:
        inventory = InventoryItem.objects.get(
            product=instance.product,
            location=instance.location
        )
    except InventoryItem.DoesNotExist:
        return  # Skip deduction if inventory doesn’t exist

    before = inventory.qty_on_hand
    new_quantity = max(0, before - instance.quantity)

    # Atomic update
    InventoryItem.objects.filter(
        product=instance.product,
        location=instance.location
    ).update(qty_on_hand=new_quantity)

    # Refresh inventory
    inventory.refresh_from_db()

    # Create stock entry
    stock_entry = StockEntry.objects.create(
        product=instance.product,
        location=instance.location,
        quantity=-instance.quantity,
        entry_type=instance.damage_type if instance.damage_type in dict(StockEntry.ENTRY_TYPES) else 'damage',
        note=f"Auto-deducted due to damage report ({instance.damage_type})",
        created_by=instance.reported_by
    )

    # Create ledger record
    StockLedger.objects.create(
        product=instance.product,
        location=instance.location,
        quantity_before=before,
        quantity_changed=-instance.quantity,
        quantity_after=inventory.qty_on_hand,
        related_entry=stock_entry
    )

    # Create audit log
    AuditLog.objects.create(
        action_type='damage_report',
        user=instance.reported_by,
        product=instance.product,
        location=instance.location,
        related_id=instance.id,
        note=f"{instance.quantity} units deducted due to {instance.damage_type} damage."
    )

    