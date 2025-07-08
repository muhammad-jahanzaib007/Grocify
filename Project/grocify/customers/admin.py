from django.contrib import admin
from .models import Customer, LoyaltyTier, CreditSale

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'phone', 'email', 'address',
        'outstanding_balance', 'points', 'tier', 'joined_at'
    )
    list_filter = ('tier', 'joined_at')
    search_fields = ('name', 'phone', 'email')
    ordering = ('-joined_at',)  # Most recent on top
    readonly_fields = ('joined_at',)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.phone == '0000000000':
            return False
        return super().has_delete_permission(request, obj)

@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_points', 'discount_percent')

@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'transaction', 'credit_amount',
        'amount_paid', 'balance_due', 'due_date',
        'is_paid', 'created_at'
    )
    list_filter = ('is_paid', 'due_date', 'created_at')
    search_fields = ('customer__name', 'customer__phone', 'transaction__id')
