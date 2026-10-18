from django.db import models
from restaurants.models import Restaurant


class Category(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['position', 'name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['restaurant', 'position']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class MenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_veg = models.BooleanField(default=True, help_text='Check if Vegetarian, uncheck for Non-Vegetarian')
    photo = models.ImageField(upload_to='dishes/', blank=True, null=True)
    tags = models.CharField(
        max_length=100,
        blank=True,
        help_text="Comma-separated tags e.g. Bestseller, Chef's Pick, Spicy"
    )
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Uncheck if sold out'
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'name']
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        indexes = [
            models.Index(fields=['restaurant', 'position']),
            models.Index(fields=['category', 'is_available']),
        ]

    def __str__(self):
        return f"{self.name} (₹{self.price})"

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
