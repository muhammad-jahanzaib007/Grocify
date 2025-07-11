from django import forms
from .models import CreditPayment, CreditSale
from customers.models import Customer

class CreditPaymentForm(forms.ModelForm):
    class Meta:
        model = CreditPayment
        fields = ['credit_sale', 'customer', 'amount_paid', 'method', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        sale = cleaned_data.get("credit_sale")
        amount = cleaned_data.get("amount_paid")

        if sale and amount:
            total_paid = sum(p.amount_paid for p in sale.payments.all())
            if amount + total_paid > sale.amount:
                raise forms.ValidationError("Total payment exceeds credit sale amount.")

        return cleaned_data