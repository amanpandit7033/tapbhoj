from django import forms
from .models import Restaurant


class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = [
            'name',
            'logo',
            'whatsapp_number',
            'address',
            'google_review_url',
            'number_of_tables',
            'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'placeholder': 'e.g. 919876543210 (with country code)'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none'
            }),
            'google_review_url': forms.URLInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'placeholder': 'https://g.page/r/.../review'
            }),
            'number_of_tables': forms.NumberInput(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
                'min': '1',
                'max': '200'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'w-full text-xs text-tapbhoj-muted dark:text-tapbhoj-muted-dark file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-tapbhoj-brand/10 file:text-tapbhoj-brand dark:file:bg-tapbhoj-accent/20 dark:file:text-tapbhoj-accent hover:file:bg-tapbhoj-brand/20'
            }),
        }
