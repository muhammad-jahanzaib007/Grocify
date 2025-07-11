from django.contrib import admin
from .models import LoyaltyProfile, PointTransaction, Reward, RewardRedemption

@admin.register(LoyaltyProfile)
class LoyaltyProfileAdmin(admin.ModelAdmin):
    list_display = ['customer', 'points', 'tier', 'lifetime_points', 'last_updated']
    search_fields = ['customer__full_name', 'tier']
    list_filter = ['tier']

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['profile', 'points', 'transaction_type', 'date', 'source']
    list_filter = ['transaction_type']
    search_fields = ['profile__customer__full_name', 'source']

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_required', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ['profile', 'reward', 'points_used', 'redeemed_on']
    search_fields = ['profile__customer__full_name', 'reward__name']