from django.contrib import admin
from .models import OwnerProfile


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'created_at')
    search_fields = ('user__username', 'user__email', 'restaurant__name')
    list_filter = ('restaurant',)
