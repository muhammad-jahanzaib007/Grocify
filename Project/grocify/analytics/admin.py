from django.contrib import admin
from .models import DamageReportSnapshot

@admin.register(DamageReportSnapshot)
class DamageReportSnapshotAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'damage_type', 'quantity', 'value_lost', 'reported_at']
    list_filter = ['damage_type', 'location', 'reported_at']
    search_fields = ['product__name', 'location__name']
    ordering = ['-reported_at']