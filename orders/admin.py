from django.contrib import admin
from .models import OrderLog


@admin.register(OrderLog)
class OrderLogAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'table_number', 'total_amount', 'status', 'items_summary', 'created_at')
    list_filter = ('restaurant', 'status', 'created_at')
    search_fields = ('restaurant__name', 'table_number', 'customer_note')
    ordering = ('-created_at',)
