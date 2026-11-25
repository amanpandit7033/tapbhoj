import re
from django.core.exceptions import ValidationError
from django.db import models


def validate_whatsapp_number(value):
    """
    Validate WhatsApp number: Country code followed by phone number digits without +, spaces, or dashes.
    E.g. 919876543210
    """
    clean_val = value.strip().lstrip('+')
    if not re.match(r'^\d{10,15}$', clean_val):
        raise ValidationError(
            'Enter a valid WhatsApp number with country code (e.g. 919876543210, 10 to 15 digits, no spaces or symbols).'
        )


def validate_upi_id(value):
    """
    Validate Indian UPI ID / VPA format: e.g. merchant@bank, 9876543210@paytm.
    """
    if value and not re.match(r'^[\w\.\-]+@[\w\-]+$', value.strip()):
        raise ValidationError(
            'Enter a valid UPI ID (e.g. restaurant@icici or 9876543210@paytm).'
        )


class Restaurant(models.Model):
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
    ]

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, db_index=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    description = models.TextField(blank=True, help_text='Short tagline or description of the restaurant.')
    whatsapp_number = models.CharField(
        max_length=20,
        validators=[validate_whatsapp_number],
        help_text='WhatsApp number with country code without + or spaces (e.g. 919876543210).'
    )
    address = models.CharField(max_length=255, blank=True)
    upi_id = models.CharField(
        max_length=100,
        blank=True,
        validators=[validate_upi_id],
        help_text='UPI VPA for zero-fee direct table payments (e.g. restaurant@icici or 9876543210@paytm).'
    )
    upi_payee_name = models.CharField(
        max_length=150,
        blank=True,
        help_text='Payee name registered on UPI / bank (e.g. Dilli Rasoi).'
    )
    google_review_url = models.URLField(blank=True, help_text='Direct link for customers to leave a Google review.')
    number_of_tables = models.PositiveIntegerField(default=10, help_text='Number of physical tables.')
    currency = models.CharField(max_length=10, default='INR')
    language = models.CharField(max_length=10, default='en')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text='Restaurant latitude for geofence validation.')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text='Restaurant longitude for geofence validation.')
    geofence_radius = models.PositiveIntegerField(default=200, help_text='Allowed ordering distance in meters (default 200m).')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Restaurant'
        verbose_name_plural = 'Restaurants'

    def __str__(self):
        return self.name

    @property
    def is_live(self):
        return self.status in ('trial', 'active')

    def clean(self):
        super().clean()
        if self.whatsapp_number:
            # Normalize WhatsApp number (remove +, spaces, hyphens)
            self.whatsapp_number = re.sub(r'[\s\+\-\(\)]', '', self.whatsapp_number)
        if self.upi_id:
            self.upi_id = self.upi_id.strip()
