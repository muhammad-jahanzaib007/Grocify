from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'category',
        'amount',
        'vendor',
        'location',
        'date',
        'created_by',
        'receipt_number'
    )
    list_filter = ('category', 'location', 'date', 'created_by')
    search_fields = ('description', 'vendor', 'receipt_number', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)