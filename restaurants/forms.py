from django import forms
from .models import Restaurant


class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = [
            'name',
            'logo',
            'whatsapp_number',
            'upi_id',
            'upi_payee_name',
            'address',
            'google_review_url',
            'number_of_tables',
            'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'e.g. 919876543210 (with country code)'
            }),
            'upi_id': forms.TextInput(attrs={
                'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'e.g. restaurant@icici or 9876543210@paytm'
            }),
            'upi_payee_name': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'e.g. Dilli Rasoi Foods'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs'
            }),
            'google_review_url': forms.URLInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'https://g.page/r/.../review'
            }),
            'number_of_tables': forms.NumberInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'min': '1',
                'max': '200'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs'
            }),
        }
