from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseItem, PurchaseReceipt, PurchaseReceiptItem

class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product', 'quantity', 'cost_price']

PurchaseItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseItem,
    form=PurchaseItemForm,
    extra=1,
    can_delete=True
)

class PurchaseReceiptItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseReceiptItem
        fields = ['purchase_item', 'quantity_received', 'quantity_damaged', 'notes']

PurchaseReceiptItemFormSet = inlineformset_factory(
    PurchaseReceipt,
    PurchaseReceiptItem,
    form=PurchaseReceiptItemForm,
    extra=0,
    can_delete=False
)