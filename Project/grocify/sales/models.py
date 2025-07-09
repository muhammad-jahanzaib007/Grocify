import uuid
from django.db import models
from django.contrib.auth.models import User
from inventory.models import Product, Location
from customers.models import Customer

class SaleTransaction(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Credit', 'On Account'),
        ('Online', 'Online Payment'),
        ('Store Points', 'Store Points'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    is_return = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Ensure a Walk-In Customer if none provided
        if not self.customer:
            self.customer = Customer.get_walkin_customer()

        # Auto-generate invoice if missing
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice #{self.invoice_number} – {self.total_amount} PKR"

class SaleItem(models.Model):
    transaction = models.ForeignKey(
        SaleTransaction,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    points_earned = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"
class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def is_valid(self):
        from django.utils import timezone
        return (self.is_active and 
                self.start_date <= timezone.now() <= self.end_date and
                self.used_count < self.max_uses)
class Return(models.Model):
    RETURN_TYPES = [
        ('full', 'Full Return'),
        ('partial', 'Partial Return'),
    ]
    
    original_transaction = models.ForeignKey(SaleTransaction, on_delete=models.CASCADE, related_name='returns')
    return_transaction = models.ForeignKey(SaleTransaction, on_delete=models.CASCADE, related_name='return_for', null=True, blank=True)
    return_type = models.CharField(max_length=20, choices=RETURN_TYPES)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return for {self.original_transaction.invoice_number}"
class ReturnItem(models.Model):
    return_record = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity_returned = models.DecimalField(max_digits=10, decimal_places=2)
    price_at_return = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Return: {self.product.name} × {self.quantity_returned}"
