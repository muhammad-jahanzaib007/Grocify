from django.contrib import admin
from .models import (
    Category, Supplier, Location, Product,
    InventoryItem, StockEntry, StockLedger, DamageReport
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'company', 'sku', 'category',
        'purchase_price', 'tax_percent', 'selling_price',
        'unit', 'points_per_unit', 'default_location', 'is_active'
    )
    list_filter = ('company', 'category', 'default_location', 'is_active')
    search_fields = ('name', 'sku', 'company')
    list_editable = ('purchase_price', 'selling_price', 'tax_percent', 'points_per_unit', 'is_active')
    readonly_fields = ('image',)

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'qty_on_hand', 'is_low_stock')
    list_filter = ('location',)
    search_fields = ('product__name', 'product__sku')
    list_editable = ('qty_on_hand',)

@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'quantity', 'entry_type', 'created_at', 'created_by')
    list_filter = ('entry_type', 'location', 'created_by')
    search_fields = ('product__name', 'note')

@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'location', 'quantity_before',
        'quantity_changed', 'quantity_after', 'timestamp'
    )
    list_filter = ('location',)
    search_fields = ('product__name',)
@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'damage_type', 'quantity', 'reported_by', 'reported_at')
    list_filter = ('damage_type', 'location', 'reported_by', 'reported_at')
    search_fields = ('product__name', 'description')
    readonly_fields = ('reported_at',)

admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Location)