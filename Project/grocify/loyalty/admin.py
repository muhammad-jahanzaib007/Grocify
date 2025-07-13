from django.contrib import admin
from .models import LoyaltyProfile, PointTransaction, Reward, RewardRedemption

class PointTransactionInline(admin.TabularInline):
    model = PointTransaction
    extra = 0
    readonly_fields = ['points', 'transaction_type', 'date', 'source']
    can_delete = False
    show_change_link = True
@admin.register(LoyaltyProfile)
class LoyaltyProfileAdmin(admin.ModelAdmin):
    list_display = ['customer', 'points', 'tier', 'lifetime_points', 'last_updated']
    search_fields = ['customer__name', 'tier__name']
    list_filter = ['tier']
    inlines = [PointTransactionInline]

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

