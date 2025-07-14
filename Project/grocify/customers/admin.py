from django.contrib import admin
from django.utils.html import format_html
from .models import Customer
from loyalty.models import LoyaltyTier
from credit.models import CreditSale

class CreditSaleInline(admin.TabularInline):
    model = CreditSale
    extra = 0
    fields = (
        'transaction',
        'credit_amount',
        'amount_paid',
        'balance_due',
        'due_date',
        'is_settled',
    )
    readonly_fields = fields
    can_delete = False
    show_change_link = True

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phone',
        'email',
        'outstanding_balance',
        'points',
        'tier_badge',
        'joined_at',
    )
    list_filter = ('tier', 'joined_at')
    search_fields = ('name', 'phone', 'email')
    ordering = ('-joined_at',)
    readonly_fields = ('joined_at',)
    inlines = [CreditSaleInline]

    def tier_badge(self, obj):
        if obj.tier:
            return format_html(
                '<span style="color:{0}; font-weight:600;">{1}</span>',
                obj.tier.badge_color,
                obj.tier.name
            )
        return "-"
    tier_badge.short_description = 'Loyalty Tier'

    def has_delete_permission(self, request, obj=None):
        if obj and obj.phone == '0000000000':
            return False
        return super().has_delete_permission(request, obj)

@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_points', 'discount_percent')
    ordering = ('-min_points',)


