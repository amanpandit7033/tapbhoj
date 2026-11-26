from django.conf import settings
from django.db import models
from restaurants.models import Restaurant


class OwnerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owner_profile'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='owners',
        help_text='The restaurant managed by this owner.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Owner Profile'
        verbose_name_plural = 'Owner Profiles'

    def __str__(self):
        return f"{self.user.username} -> {self.restaurant.name}"


class StaffMember(models.Model):
    """
    Represents a staff member (Manager, Cashier, Waiter, Kitchen) belonging to a single Restaurant.
    Optionally linked to a Django User so they can log in to the Store Dashboard.
    """
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('waiter', 'Waiter / Server'),
        ('kitchen', 'Kitchen / Chef'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='staff_members'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        null=True,
        blank=True,
        help_text='Optional login user for dashboard access.'
    )
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='waiter')
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) - {self.restaurant.name}"
