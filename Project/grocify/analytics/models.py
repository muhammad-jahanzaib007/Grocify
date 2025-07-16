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

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPES)
    quantity = models.PositiveIntegerField()
    value_lost = models.DecimalField(max_digits=10, decimal_places=2)
    reported_at = models.DateTimeField()
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    related_purchase = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)

    snapshot_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.product.name} – {self.damage_type} × {self.quantity} @ {self.location.name}"