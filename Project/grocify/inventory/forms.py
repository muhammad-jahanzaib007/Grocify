from django import forms
from .models import Product, Category, Supplier, Location, StockEntry

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'company', 'sku', 'category', 'supplier',
            'purchase_price', 'tax_percent', 'selling_price',
            'unit', 'points_per_unit', 'default_location',
            'image', 'is_active'
        ]
        widgets = {
            'image': forms.ClearableFileInput(),
        }
class StockAdjustmentForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        label="Product"
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        label="Location"
    )
    quantity_change = forms.IntegerField(
        label="Quantity Change",
        help_text="Use negative numbers to deduct stock"
    )
    reason = forms.ChoiceField(
        choices=StockEntry._meta.get_field('entry_type').choices,
        label="Reason"
    )
    note = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Note"
    )
