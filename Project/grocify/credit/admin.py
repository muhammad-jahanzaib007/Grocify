from django.contrib import admin
from .models import CreditSale, CreditPayment, CreditLedger

@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'amount', 'issued_on', 'due_date', 'is_settled']
    list_filter = ['is_settled', 'due_date']
    search_fields = ['customer__full_name', 'note']
    date_hierarchy = 'issued_on'


@admin.register(CreditPayment)
class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount_paid', 'paid_on', 'method']
    list_filter = ['method', 'paid_on']
    search_fields = ['customer__full_name', 'note']


@admin.register(CreditLedger)
class CreditLedgerAdmin(admin.ModelAdmin):
    list_display = ['customer', 'action', 'amount', 'timestamp']
    search_fields = ['customer__full_name', 'action', 'note']
    date_hierarchy = 'timestamp'