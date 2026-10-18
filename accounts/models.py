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
