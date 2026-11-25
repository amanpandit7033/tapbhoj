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
            'latitude',
            'longitude',
            'geofence_radius',
            'description',
        ]
        widgets = {
            'latitude': forms.NumberInput(attrs={
                'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'e.g. 28.613939',
                'step': '0.000001'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': 'e.g. 77.209021',
                'step': '0.000001'
            }),
            'geofence_radius': forms.NumberInput(attrs={
                'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs',
                'placeholder': '200'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:ring-2 focus:ring-primary-600 focus:outline-none shadow-xs'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'w-full text-xs text-slate-500 file:mr-3.5 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer file:transition-colors',
                'accept': 'image/*'
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
