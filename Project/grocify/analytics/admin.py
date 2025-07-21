from django.contrib import admin
from .models import DamageReportSnapshot
from .models import PurchaseReportSnapshot


@admin.register(DamageReportSnapshot)
class DamageReportSnapshotAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'damage_type', 'quantity', 'value_lost', 'reported_at']
    list_filter = ['damage_type', 'location', 'reported_at']
    search_fields = ['product__name', 'location__name']
    ordering = ['-reported_at']


@admin.register(PurchaseReportSnapshot)
class PurchaseReportSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'location',
        'total_orders', 'total_qty_ordered', 'total_cost',
        'generated_at'
    ]
    list_filter = ['location', 'date']
    ordering = ['-date']
