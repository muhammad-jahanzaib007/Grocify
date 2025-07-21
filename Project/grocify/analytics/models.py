from django.db import models
from django.contrib.auth.models import User
from inventory.models import Product, Location
from purchases.models import PurchaseOrder  # Optional for related_purchase reference

class DamageReportSnapshot(models.Model):
    DAMAGE_TYPES = [
        ('received_damaged', 'Received Damaged'),
        ('in_store_damage', 'In-Store Damage'),
        ('expired', 'Expired'),
        ('theft', 'Theft'),
        ('spoilage', 'Spoilage'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='damage_reports')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='damage_reports')
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPES)
    quantity = models.PositiveIntegerField()
    value_lost = models.DecimalField(max_digits=10, decimal_places=2)
    reported_at = models.DateTimeField()
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_reports')
    related_purchase = models.ForeignKey('purchases.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_reports')

    snapshot_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['reported_at', 'location']),
            models.Index(fields=['product', 'location']),
            models.Index(fields=['damage_type', 'reported_at']),
        ]

    def __str__(self):
        return f"{self.product.name} – {self.damage_type} × {self.quantity} @ {self.location.name}"
class PurchaseReportSnapshot(models.Model):
    date              = models.DateField()
    location          = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='purchase_reports')
    total_orders      = models.PositiveIntegerField()
    total_qty_ordered = models.PositiveIntegerField()
    total_cost        = models.DecimalField(max_digits=12, decimal_places=2)
    generated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('date', 'location')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'location']),
            models.Index(fields=['generated_at']),
        ]

    def __str__(self):
        return f"PO @ {self.location.name} on {self.date}"
