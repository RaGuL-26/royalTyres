from django.db import models
from django.contrib.auth.models import User


class Tyre(models.Model):
    BRAND_CHOICES = [
        ('CEAT', 'CEAT'),
        ('APOLLO', 'APOLLO'),
        ('JK', 'JK'),
    ]

    TUBE_TYPE_CHOICES = [
        ('Tube', 'Tube'),
        ('Tubeless', 'Tubeless'),
    ]

    brand = models.CharField(max_length=50, choices=BRAND_CHOICES)
    model_with_size = models.CharField(max_length=150)  # e.g., "Secura Drive 195/55 R16"
    tube_type = models.CharField(max_length=20, choices=TUBE_TYPE_CHOICES)

    # Shop stocks
    quantity_TS = models.PositiveIntegerField(default=0, verbose_name="Tirupur Stock")
    quantity_GS = models.PositiveIntegerField(default=0, verbose_name="Gobi Stock")

    # Pricing
    invoice_price = models.DecimalField(max_digits=10, decimal_places=2)
    amazon_listed = models.BooleanField(default=False)
    amazon_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.brand} - {self.model_with_size} ({self.tube_type})"


class SaleLog(models.Model):
    SHOP_CHOICES = [
        ('TS', 'Tirupur Shop'),
        ('GS', 'Gobi Shop'),
    ]
    CUSTOMER_CHOICES = [
        ('Amazon', 'Amazon'),
        ('Retail', 'Retail'),
    ]

    tyre = models.ForeignKey(Tyre, on_delete=models.CASCADE, related_name="sales")
    shop_code = models.CharField(max_length=2, choices=SHOP_CHOICES)
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_CHOICES)
    customer_name = models.CharField(max_length=100, blank=True, null=True)

    quantity_sold = models.PositiveIntegerField()

    # Prices captured at the time of sale
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)      # Amazon or Retail unit price used
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)     # unit_price * qty
    profit = models.DecimalField(max_digits=12, decimal_places=2)           # total_amount - (invoice_price * qty)

    sold_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.tyre} | {self.get_shop_code_display()} | {self.customer_type} | {self.quantity_sold} @ {self.unit_price}"




