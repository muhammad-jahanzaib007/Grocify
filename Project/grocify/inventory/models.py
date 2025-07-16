from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
class Supplier(models.Model):
    name = models.CharField(max_length=100, verbose_name="Company Name")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Representative Name")
    email = models.EmailField(blank=True, verbose_name="Company Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Company Phone")
    company_address = models.TextField(blank=True)
    vendor_address = models.TextField(blank=True)
    vendor_phone = models.CharField(max_length=20, blank=True)
    representative_phone = models.CharField(max_length=20, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
class Product(models.Model):
    UNIT_CHOICES = [
        ('pcs', 'Pieces'), ('kg', 'Kilograms'), ('lbs', 'Pounds'),
        ('ltr', 'Liters'), ('gal', 'Gallons'), ('box', 'Box'),
        ('case', 'Case'), ('pack', 'Pack'),
    ]

    name = models.CharField(max_length=100, verbose_name="Product Name")
    company = models.CharField(max_length=100, blank=True, verbose_name="Company Name")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Barcode")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reorder_level = models.PositiveIntegerField(default=10)
    max_stock_level = models.PositiveIntegerField(null=True, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pcs')
    points_per_unit = models.PositiveIntegerField(default=0)
    default_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def selling_price_with_tax(self):
        return self.selling_price * (1 + self.tax_percent / 100)

    @property
    def profit_margin(self):
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0

class InventoryItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    qty_on_hand = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    last_counted = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('product', 'location')
        ordering = ['product__name', 'location__name']

    def __str__(self):
        return f"{self.product.name} @ {self.location.name} ({self.qty_on_hand})"

    def is_low_stock(self):
        return self.qty_on_hand <= self.product.reorder_level

    def is_overstocked(self):
        if self.product.max_stock_level:
            return self.qty_on_hand > self.product.max_stock_level
        return False

    @property
    def stock_value(self):
        return self.qty_on_hand * self.product.purchase_price

class StockEntry(models.Model):
    ENTRY_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('adjustment', 'Adjustment'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('damage', 'Damaged Goods'),
        ('theft', 'Stolen'),
        ('return', 'Return'),
        ('expired', 'Expired'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='purchase')
    reference_number = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        display_type = dict(self.ENTRY_TYPES).get(self.entry_type, self.entry_type.title())
        return f"{display_type} {abs(self.quantity)} × {self.product.name} @ {self.location.name}"

class StockLedger(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity_before = models.IntegerField()
    quantity_changed = models.IntegerField()
    quantity_after = models.IntegerField()
    related_entry = models.ForeignKey(StockEntry, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.product.name} @ {self.location.name}: {self.quantity_before} → {self.quantity_after}"

class DamageReport(models.Model):
    DAMAGE_TYPES = [
        ('received_damaged', 'Received Damaged'), ('in_store_damage', 'In-Store Damage'),
        ('expired', 'Expired'), ('theft', 'Theft'), ('spoilage', 'Spoilage'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPES)
    quantity = models.PositiveIntegerField()
    value_lost = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    related_purchase = models.ForeignKey('purchases.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"Damage: {self.product.name} × {self.quantity} ({self.damage_type})"

class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_date = models.DateTimeField(auto_now_add=True)
    purchase_order = models.ForeignKey('purchases.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('product', 'location', 'batch_number')
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.product.name} - Batch {self.batch_number}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date and self.expiry_date < timezone.now().date()

    @property
    def days_to_expiry(self):
        if self.expiry_date:
            from django.utils import timezone
            return (self.expiry_date - timezone.now().date()).days
        return None

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('stock_adjustment', 'Stock Adjustment'),
        ('damage_report', 'Damage Report'),
        ('stock_entry', 'Stock Entry'),
        ('stock_ledger', 'Ledger Update'),
        ('inventory_edit', 'Inventory Edit'),
        ('product_edit', 'Product Edit'),
        ('purchase_received', 'Purchase Received'),
        ('manual_override', 'Manual Override'),
        ('delete_action', 'Delete Action'),
        ('other', 'Other'),
    ]

    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    related_id = models.PositiveIntegerField(null=True, blank=True, help_text="Optional ID of related model instance")
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        target = f"{self.product.name}" if self.product else "No Product"
        loc = f"@ {self.location.name}" if self.location else "N/A"
        return f"{self.get_action_type_display()} — {target} {loc}"
