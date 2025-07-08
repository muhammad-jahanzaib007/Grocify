from django.contrib import admin
from .models import (
    SaleTransaction, SaleItem,
    Coupon, Return, ReturnItem
)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'cashier', 'customer',
        'location', 'payment_method',
        'total_amount', 'amount_paid',
        'change_due', 'date'
    )
    list_filter = ('location', 'payment_method', 'cashier')
    search_fields = ('invoice_number', 'customer__name', 'customer__phone')
    inlines = [SaleItemInline]
    date_hierarchy = 'date'

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'discount_type', 'discount_value',
        'minimum_amount', 'used_count', 'max_uses',
        'is_active', 'start_date', 'end_date'
    )
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at',)

class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = (
        'original_transaction', 'return_type',
        'return_amount', 'processed_by', 'processed_at'
    )
    list_filter = ('return_type', 'processed_by')
    search_fields = ('original_transaction__invoice_number', 'reason')
    inlines = [ReturnItemInline]
    date_hierarchy = 'processed_at'