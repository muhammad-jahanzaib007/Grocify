from django.contrib import admin
from .models import CreditSale, CreditPayment, CreditLedger

@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'transaction',
        'credit_amount',
        'amount_paid',
        'balance_due',
        'due_date',
        'is_settled',
        'issued_on',
    )
    list_filter = ('is_settled', 'due_date', 'issued_on')
    search_fields = (
        'customer__name',
        'customer__phone',
        'transaction__invoice_number',
    )
    ordering = ('-issued_on',)


@admin.register(CreditPayment)
class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'credit_sale',
        'customer',
        'amount_paid',
        'method',
        'paid_on',
    )
    list_filter = ('method', 'paid_on')
    search_fields = ('customer__name', 'credit_sale__transaction__invoice_number')
    ordering = ('-paid_on',)


@admin.register(CreditLedger)
class CreditLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'action',
        'amount',
        'timestamp',
        'related_sale',
    )
    list_filter = ('action', 'timestamp')
    search_fields = ('customer__name', 'related_sale__transaction__invoice_number')
    ordering = ('-timestamp',)
