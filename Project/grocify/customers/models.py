from django.db import models

class LoyaltyTier(models.Model):
    name = models.CharField(max_length=50)
    min_points = models.PositiveIntegerField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name} – {self.discount_percent}% off"


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    points = models.PositiveIntegerField(default=0)
    tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def update_tier(self):
        """
        Assigns the highest LoyaltyTier matching this customer's point balance.
        """
        applicable = LoyaltyTier.objects.filter(min_points__lte=self.points).order_by('-min_points').first()
        if applicable and self.tier != applicable:
            self.tier = applicable
            self.save()

    @classmethod
    def get_walkin_customer(cls):
        """
        Returns the singleton 'Walk-In Customer' object.
        Creates it if not found.
        """
        return cls.objects.get_or_create(
            phone='0000000000',
            defaults={'name': 'Walk-In Customer'}
        )[0]
class CreditSale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='credit_sales')
    transaction = models.ForeignKey('sales.SaleTransaction', on_delete=models.CASCADE)
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Credit: {self.customer.name} - {self.balance_due}"