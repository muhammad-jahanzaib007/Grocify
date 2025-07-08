from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    company_address = models.TextField(blank=True)
    vendor_address = models.TextField(blank=True)  # Different from company
    vendor_phone = models.CharField(max_length=20, blank=True)
    representative_phone = models.CharField(max_length=20, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)  # NEW: item company
    sku = models.CharField(max_length=50, unique=True, verbose_name="Barcode / SKU")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # NEW: tax
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level = models.PositiveIntegerField(default=10)
    unit = models.CharField(max_length=20, default='pcs')
    points_per_unit = models.PositiveIntegerField(default=0)  # NEW: customer reward logic
    default_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)  # NEW: default location
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

class InventoryItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    qty_on_hand = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'location')

    def __str__(self):
        return f"{self.product.name} @ {self.location.name}"

    def is_low_stock(self):
        return self.qty_on_hand <= self.product.reorder_level

class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.IntegerField()  # Can be negative (for shrink)
    entry_type = models.CharField(
        max_length=20,
        choices=[
            ('purchase', 'Purchase'),
            ('adjustment', 'Adjustment'),
            ('transfer', 'Transfer'),
            ('damage', 'Damaged Goods'),
            ('theft', 'Stolen'),
        ],
        default='purchase'
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.entry_type.upper()} {self.quantity} {self.product} @ {self.location}"

class StockLedger(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity_before = models.IntegerField()
    quantity_changed = models.IntegerField()
    quantity_after = models.IntegerField()
    related_entry = models.ForeignKey(StockEntry, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} @ {self.location.name}: {self.quantity_before} → {self.quantity_after}"
class DamageReport(models.Model):
    DAMAGE_TYPES = [
        ('received_damaged', 'Received Damaged'),
        ('in_store_damage', 'In-Store Damage'),
        ('expired', 'Expired'),
        ('theft', 'Theft'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPES)
    quantity = models.PositiveIntegerField()
    value_lost = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    
    # Link to purchase if damaged on receipt
    related_purchase = models.ForeignKey('purchases.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Damage: {self.product.name} × {self.quantity}"
