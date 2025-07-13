from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, CreditSale
from loyalty.models import LoyaltyTier

class CreditSaleInline(admin.TabularInline):
    model = CreditSale
    extra = 0
    fields = ('transaction', 'credit_amount', 'amount_paid', 'balance_due', 'due_date', 'is_paid')
    readonly_fields = fields
    can_delete = False
    show_change_link = True

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'phone', 'email', 'outstanding_balance',
        'points', 'tier_badge', 'joined_at'
    )
    list_filter = ('tier', 'joined_at')
    search_fields = ('name', 'phone', 'email')
    ordering = ('-joined_at',)
    readonly_fields = ('joined_at',)
    inlines = [CreditSaleInline]

    def tier_badge(self, obj):
        if obj.tier:
            return format_html(
                '<span style="color:#1abc9c; font-weight:600;">{}</span>',
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

@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'transaction', 'credit_amount',
        'amount_paid', 'balance_due', 'due_date',
        'is_paid', 'created_at'
    )
    list_filter = ('is_paid', 'due_date', 'created_at')
    search_fields = ('customer__name', 'customer__phone', 'transaction__invoice_number')
    ordering = ('-created_at',)