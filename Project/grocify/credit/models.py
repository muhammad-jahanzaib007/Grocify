# credit/models.py

from decimal import Decimal, InvalidOperation
from django.db import models
from django.utils import timezone
from customers.models import Customer
from sales.models import SaleTransaction

class CreditSale(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='credit_sales'
    )
    transaction = models.OneToOneField(
        SaleTransaction,
        on_delete=models.CASCADE,
        related_name='credit_sale'
    )
    credit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    issued_on = models.DateTimeField(
        default=timezone.now
    )
    due_date = models.DateField()
    is_settled = models.BooleanField(
        default=False,
        help_text="Marked true once balance_due reaches zero"
    )
    note = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-issued_on']
        verbose_name = 'Credit Sale'
        verbose_name_plural = 'Credit Sales'

    def __str__(self):
        return f"CreditSale #{self.id} — {self.customer.name} — Rs. {self.credit_amount}"

    @property
    def balance_due(self):
        """
        Remaining amount to be paid. Ensure both sides are Decimal.
        """
        # Safely convert even floats or None to Decimal
        try:
            credit = Decimal(str(self.credit_amount))
        except (TypeError, InvalidOperation):
            credit = Decimal('0.00')

        try:
            paid = Decimal(str(self.amount_paid))
        except (TypeError, InvalidOperation):
            paid = Decimal('0.00')

        remaining = credit - paid
        return remaining if remaining > Decimal('0.00') else Decimal('0.00')

    def save(self, *args, **kwargs):
        # Auto‐settle if fully paid
        if self.balance_due == Decimal('0.00'):
            self.is_settled = True

        super().save(*args, **kwargs)

        # Recalculate customer's outstanding balance
        self.customer.recalculate_outstanding()


class CreditPayment(models.Model):
    credit_sale = models.ForeignKey(
        CreditSale,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    paid_on = models.DateTimeField(
        default=timezone.now
    )
    method = models.CharField(
        max_length=50,
        choices=[
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('bank', 'Bank Transfer'),
            ('mobile', 'Mobile Wallet'),
            ('other', 'Other'),
        ]
    )
    note = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-paid_on']
        verbose_name = 'Credit Payment'
        verbose_name_plural = 'Credit Payments'

    def __str__(self):
        return f"Rs. {self.amount_paid} — {self.customer.name} — {self.method}"


class CreditLedger(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )
    action = models.CharField(
        max_length=100,
        help_text="e.g., 'New Credit Sale', 'Partial Payment'"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    timestamp = models.DateTimeField(
        auto_now_add=True
    )
    related_sale = models.ForeignKey(
        CreditSale,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    note = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Credit Ledger Entry'
        verbose_name_plural = 'Credit Ledger Entries'

    def __str__(self):
        return f"{self.customer.name} — {self.action} ({self.amount})"