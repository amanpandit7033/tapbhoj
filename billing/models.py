from datetime import timedelta
from django.db import models
from django.utils import timezone
from restaurants.models import Restaurant


class Plan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='Price in INR (₹)')
    duration_days = models.PositiveIntegerField(default=30, help_text='Duration of the billing cycle in days')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} - ₹{self.price:.0f}/{self.duration_days} days"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
    ]

    restaurant = models.OneToOneField(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing', db_index=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_status_display()}"

    @property
    def expiry_date(self):
        if self.status == 'trialing' and self.trial_end:
            return self.trial_end
        return self.current_period_end

    @property
    def is_valid(self):
        """Returns True if the subscription is currently active or in trial and unexpired."""
        if self.status not in ('trialing', 'active'):
            return False
        expiry = self.expiry_date
        if expiry and timezone.now() > expiry:
            return False
        return True

    @property
    def days_remaining(self):
        expiry = self.expiry_date
        if not expiry:
            return None
        delta = expiry - timezone.now()
        return max(0, delta.days)

    def activate_trial(self, trial_days=14):
        """Start a free trial for the given number of days."""
        now = timezone.now()
        self.status = 'trialing'
        self.trial_start = now
        self.trial_end = now + timedelta(days=trial_days)
        self.save()

    def renew(self, plan, payment_id=None, order_id=None):
        """Renew subscription for the specified plan."""
        now = timezone.now()
        # If current period is still active, extend from end date, else from now
        start_date = self.current_period_end if (self.current_period_end and self.current_period_end > now) else now
        self.plan = plan
        self.status = 'active'
        self.current_period_start = start_date
        self.current_period_end = start_date + timedelta(days=plan.duration_days)
        if payment_id:
            self.razorpay_payment_id = payment_id
        if order_id:
            self.razorpay_order_id = order_id
        self.save()

        # Ensure restaurant is marked active
        if self.restaurant.status != 'active':
            self.restaurant.status = 'active'
            self.restaurant.save(update_fields=['status'])
