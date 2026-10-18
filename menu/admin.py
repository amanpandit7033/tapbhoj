from django.contrib import admin
from .models import Category, MenuItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('name', 'price', 'is_veg', 'is_available', 'tags', 'position')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'position', 'is_visible')
    list_filter = ('restaurant', 'is_visible')
    search_fields = ('name', 'restaurant__name')
    ordering = ('restaurant', 'position')
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'is_veg', 'is_available', 'position')
    list_filter = ('restaurant', 'category', 'is_veg', 'is_available')
    search_fields = ('name', 'description', 'restaurant__name', 'tags')
    list_editable = ('price', 'is_available', 'position')
    ordering = ('restaurant', 'category', 'position')
