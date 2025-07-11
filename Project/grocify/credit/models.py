from django.db import models
from django.utils import timezone
from customers.models import Customer
from sales.models import SaleTransaction


# ─── CREDIT SALE ────────────────────────────────────────────────────────────────
class CreditSale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='credit_sales_credit')
    sale = models.OneToOneField(SaleTransaction, on_delete=models.CASCADE, related_name='credit_sale_record')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_on = models.DateTimeField(default=timezone.now)
    due_date = models.DateField()
    is_settled = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"CreditSale #{self.id} | {self.customer.full_name} | Rs. {self.amount}"


# ─── CREDIT PAYMENT ─────────────────────────────────────────────────────────────
class CreditPayment(models.Model):
    credit_sale = models.ForeignKey(CreditSale, on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
        ('mobile', 'Mobile Wallet'),
        ('other', 'Other')
    ])
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Rs. {self.amount_paid} | {self.customer.full_name} | {self.method}"


# ─── CREDIT LEDGER (OPTIONAL) ───────────────────────────────────────────────────
class CreditLedger(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)  # e.g., 'New Credit Sale', 'Partial Payment'
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_sale = models.ForeignKey(CreditSale, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.customer.full_name} — {self.action} ({self.amount})"