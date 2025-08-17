from django import forms
from .models import Tyre


class TyreForm(forms.ModelForm):
    class Meta:
        model = Tyre
        fields = [
            'brand', 'model_with_size', 'tube_type',
            'quantity_TS', 'quantity_GS',
            'invoice_price', 'amazon_listed', 'amazon_price'
        ]

    def clean(self):
        cleaned = super().clean()
        amazon_listed = cleaned.get('amazon_listed')
        amazon_price = cleaned.get('amazon_price')
        if amazon_listed and (amazon_price is None):
            raise forms.ValidationError("Amazon price is required if the tyre is listed on Amazon.")
        return cleaned


class TyreEditForm(forms.ModelForm):
    class Meta:
        model = Tyre
        fields = ['invoice_price', 'amazon_listed', 'amazon_price']

    def clean(self):
        cleaned = super().clean()
        amazon_listed = cleaned.get('amazon_listed')
        amazon_price = cleaned.get('amazon_price')
        if amazon_listed and (amazon_price is None):
            raise forms.ValidationError("Amazon price is required if the tyre is listed on Amazon.")
        return cleaned


class SellForm(forms.Form):
    CUSTOMER_CHOICES = [
        ('Amazon', 'Amazon'),
        ('Retail', 'Retail'),
    ]
    customer_type = forms.ChoiceField(choices=CUSTOMER_CHOICES)
    customer_name = forms.CharField(max_length=100, required=False)
    quantity = forms.IntegerField(min_value=1)
    custom_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
