from decimal import Decimal
from django.db import models
from django.core.validators import RegexValidator
from loyalty.models import LoyaltyTier  # Correct import from loyalty app

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Invalid phone number format')]
    )
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    outstanding_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    points = models.PositiveIntegerField(default=0)
    tier = models.ForeignKey(
        LoyaltyTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def recalculate_outstanding(self):
        """
        Sum balance_due for all unsettled credit sales
        and update the outstanding_balance field.
        """
        unsettled = self.credit_sales.filter(is_settled=False)
        total_due = sum(sale.balance_due for sale in unsettled)
        self.outstanding_balance = Decimal(total_due)
        self.save(update_fields=['outstanding_balance'])

    @classmethod
    def get_walkin_customer(cls):
        return cls.objects.get_or_create(
            phone='0000000000',
            defaults={'name': 'Walk-In Customer'}
        )[0]

    class Meta:
        ordering = ['name']