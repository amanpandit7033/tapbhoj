from django.db import models
from restaurants.models import Restaurant


class OrderLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent to WhatsApp'),
        ('preparing', 'Preparing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    table_number = models.CharField(max_length=20, db_index=True)
    items_json = models.JSONField(
        default=list,
        help_text='JSON list of item details, quantities, and prices at time of order.'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    customer_note = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='sent',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order Record'
        verbose_name_plural = 'Order Records'
        indexes = [
            models.Index(fields=['restaurant', '-created_at']),
            models.Index(fields=['restaurant', 'table_number']),
            models.Index(fields=['restaurant', 'status']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - Table {self.table_number} (₹{self.total_amount:.0f})"

    @property
    def items_summary(self):
        """Returns compact text summary of ordered items."""
        if not self.items_json:
            return "No items"
        parts = []
        for item in self.items_json:
            name = item.get('name', 'Item')
            qty = item.get('quantity', 1)
            parts.append(f"{qty}x {name}")
        return ", ".join(parts)

    @property
    def total_quantity(self):
        """Sum of all item quantities in the order."""
        if not self.items_json:
            return 0
        return sum(item.get('quantity', 1) for item in self.items_json)
