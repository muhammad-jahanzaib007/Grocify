from django.db import models
from django.utils import timezone

# ✅ Use string reference to avoid circular import
class LoyaltyProfile(models.Model):
    customer = models.OneToOneField(
        'customers.Customer',  # Lazy reference to break circular import
        on_delete=models.CASCADE,
        related_name='loyalty'
    )
    points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    tier = models.ForeignKey('LoyaltyTier', on_delete=models.SET_NULL, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.name} — {self.tier.name if self.tier else 'No Tier'} ({self.points} pts)"

    def assign_tier(self):
        new_tier = LoyaltyTier.objects.filter(min_points__lte=self.points).order_by('-min_points').first()
        if new_tier != self.tier:
            self.tier = new_tier
            self.save(update_fields=['tier'])

        if self.customer.tier != new_tier:
            self.customer.tier = new_tier
            self.customer.save(update_fields=['tier'])

    def sync_customer_summary(self):
        if self.customer.points != self.points:
            self.customer.points = self.points
            self.customer.save(update_fields=['points'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.assign_tier()
        self.sync_customer_summary()


class LoyaltyTier(models.Model):
    name = models.CharField(max_length=50)
    min_points = models.PositiveIntegerField()
    badge_color = models.CharField(max_length=20, default='gray')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name} — {self.min_points} pts"

    class Meta:
        ordering = ['-min_points']


class PointTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('earned', 'Earned'),
        ('redeemed', 'Redeemed'),
        ('adjusted', 'Manual Adjustment'),
    ]

    profile = models.ForeignKey(LoyaltyProfile, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateTimeField(default=timezone.now)
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    source = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.points} pts — {self.transaction_type} for {self.profile.customer.name}"


class Reward(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points_required = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.points_required} pts)"


class RewardRedemption(models.Model):
    profile = models.ForeignKey(LoyaltyProfile, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(Reward, on_delete=models.SET_NULL, null=True)
    points_used = models.IntegerField()
    redeemed_on = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.reward.name} redeemed for {self.points_used} pts"