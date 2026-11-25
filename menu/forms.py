from django import forms
from .models import Category, MenuItem


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'position', 'is_visible']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'e.g. Starters, Main Course, Drinks'
            }),
            'position': forms.NumberInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'min': '0'
            }),
            'is_visible': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded text-primary-600 focus:ring-primary-600 border-slate-300'
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
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'e.g. Paneer Butter Masala'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'Short description of the dish and ingredients'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full text-xs rounded-xl !pl-8 pr-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'step': '1',
                'min': '0',
                'placeholder': '0'
            }),
            'is_veg': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded text-emerald-600 focus:ring-emerald-600 border-slate-300'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded text-primary-600 focus:ring-primary-600 border-slate-300'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'Comma-separated, e.g. Bestseller, Chef Pick, Spicy'
            }),
            'position': forms.NumberInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'min': '0'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer'
            }),
        }

    def __init__(self, *args, restaurant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if restaurant:
            # Multi-tenancy guard: Only show categories belonging to this restaurant
            self.fields['category'].queryset = restaurant.categories.all()
