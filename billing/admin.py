from django.contrib import admin
from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'plan', 'status', 'trial_end', 'current_period_end', 'is_valid')
    list_filter = ('status', 'plan')
    search_fields = ('restaurant__name', 'restaurant__slug', 'razorpay_payment_id')
