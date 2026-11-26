from django.db import models
from restaurants.models import Restaurant


class OrderLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Order Received'),
        ('preparing', 'Preparing in Kitchen'),
        ('served', 'Served to Table'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('pending', 'Payment Pending Verification'),
        ('paid', 'Paid (Verified)'),
        ('rejected', 'Payment Rejected'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    session = models.ForeignKey(
        'TableSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text='Active table dining session this order belongs to.'
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
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        db_index=True
    )
    payment_method = models.CharField(
        max_length=20,
        default='upi_direct'
    )
    upi_utr = models.CharField(
        max_length=30,
        blank=True,
        help_text='Customer-submitted UPI reference / UTR number'
    )
    payment_requested = models.BooleanField(
        default=False,
        help_text='True when admin / waiter clicks Request Payment after serving.'
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True
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
            models.Index(fields=['restaurant', 'payment_status']),
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


class TableSession(models.Model):
    """
    Represents an active dining session for a table at a restaurant,
    enabling collaborative group cart ordering across multiple customer phones.
    """
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='table_sessions'
    )
    table_number = models.CharField(max_length=20, db_index=True)
    session_token = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text='Unique session key passed on QR code / session cookie to identify active physical diners.'
    )
    passcode = models.CharField(
        max_length=6,
        blank=True,
        help_text='4-digit daily passcode for waiter verification or table opening.'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    active_diners = models.JSONField(
        default=list,
        blank=True,
        help_text='List of active diner names seated at this table.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'table_number', 'is_active']),
        ]

    def __str__(self):
        return f"{self.restaurant.slug} - Table {self.table_number} ({'Active' if self.is_active else 'Closed'})"

    def get_cart_payload(self):
        """Returns cart payload formatted for frontend Alpine.js and WebSockets."""
        items = {}
        for cart_item in self.cart_items.select_related('menu_item').all():
            m = cart_item.menu_item
            items[str(m.id)] = {
                'id': m.id,
                'name': m.name,
                'price': float(m.price),
                'quantity': cart_item.quantity,
                'is_veg': m.is_veg,
                'added_by': cart_item.added_by,
            }
        return items


class TableCartItem(models.Model):
    """
    A live cart item in a shared TableSession.
    """
    session = models.ForeignKey(
        TableSession,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    menu_item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.CASCADE,
        related_name='live_cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_by = models.CharField(max_length=100, default='Guest')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['session', 'menu_item'], name='unique_session_menu_item')
        ]

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} (by {self.added_by})"


    @property
    def total_quantity(self):
        """Sum of all item quantities in the order."""
        if not self.items_json:
            return 0
        return sum(item.get('quantity', 1) for item in self.items_json)
