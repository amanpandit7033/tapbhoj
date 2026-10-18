from django import forms
from .models import Category, MenuItem


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'position', 'is_visible']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'placeholder': 'e.g. Starters, Main Course, Drinks'
            }),
            'position': forms.NumberInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'min': '0'
            }),
            'is_visible': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded text-tapbhoj-brand dark:text-tapbhoj-accent focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent border-black/10 dark:border-white/10'
            }),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'category',
            'name',
            'description',
            'price',
            'is_veg',
            'photo',
            'tags',
            'is_available',
            'position',
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'placeholder': 'e.g. Paneer Butter Masala'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'placeholder': 'Short description of the dish and ingredients'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'step': '1',
                'min': '0',
                'placeholder': '₹'
            }),
            'is_veg': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded text-tapbhoj-veg focus:ring-tapbhoj-veg border-black/10 dark:border-white/10'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded text-tapbhoj-brand dark:text-tapbhoj-accent focus:ring-tapbhoj-brand border-black/10 dark:border-white/10'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'placeholder': 'Comma-separated, e.g. Bestseller, Chef Pick, Spicy'
            }),
            'position': forms.NumberInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'min': '0'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full text-xs text-tapbhoj-muted dark:text-tapbhoj-muted-dark file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-tapbhoj-brand/10 file:text-tapbhoj-brand dark:file:bg-tapbhoj-accent/20 dark:file:text-tapbhoj-accent hover:file:bg-tapbhoj-brand/20'
            }),
        }

    def __init__(self, *args, restaurant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if restaurant:
            # Multi-tenancy guard: Only show categories belonging to this restaurant
            self.fields['category'].queryset = restaurant.categories.all()
