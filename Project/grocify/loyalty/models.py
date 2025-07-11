from django.db import models
from django.utils import timezone
from customers.models import Customer


# ─── LOYALTY PROFILE ─────────────────────────────────────────────────────────────
class LoyaltyProfile(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='loyalty')
    points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)

    tier = models.CharField(max_length=50, blank=True, null=True)  # e.g. Bronze, Silver, Gold
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.full_name} — {self.tier or 'No Tier'} ({self.points} pts)"


# ─── POINT TRANSACTIONS ──────────────────────────────────────────────────────────
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
    source = models.CharField(max_length=100, blank=True, null=True)  # e.g., Sale #1234 or Event
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.points} pts — {self.transaction_type} for {self.profile.customer.full_name}"


# ─── REWARD CATALOG ──────────────────────────────────────────────────────────────
class Reward(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points_required = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.points_required} pts)"


# ─── REWARD REDEMPTIONS ──────────────────────────────────────────────────────────
class RewardRedemption(models.Model):
    profile = models.ForeignKey(LoyaltyProfile, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(Reward, on_delete=models.SET_NULL, null=True)
    points_used = models.IntegerField()
    redeemed_on = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.reward.name} redeemed for {self.points_used} pts"