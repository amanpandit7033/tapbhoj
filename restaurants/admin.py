from django.contrib import admin
from .models import Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'whatsapp_number', 'status', 'number_of_tables', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'slug', 'whatsapp_number')
    prepopulated_fields = {'slug': ('name',)}
