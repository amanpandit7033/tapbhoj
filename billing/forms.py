from django import forms
from django.contrib.auth.models import User
from restaurants.models import Restaurant
from .models import Plan, Subscription


class RestaurantOnboardForm(forms.Form):
    # Restaurant details
    restaurant_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs',
            'placeholder': 'e.g. Royal Punjab Dhaba'
        })
    )
    slug = forms.SlugField(
        max_length=150,
        help_text='Unique URL identifier: tapbhoj.in/r/<slug>/',
        widget=forms.TextInput(attrs={
            'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs',
            'placeholder': 'royal-punjab-dhaba'
        })
    )
    whatsapp_number = forms.CharField(
        max_length=20,
        help_text='With country code, no + or spaces (e.g. 919876543210)',
        widget=forms.TextInput(attrs={
            'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs',
            'placeholder': '919876543210'
        })
    )
    number_of_tables = forms.IntegerField(
        initial=10,
        min_value=1,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs',
            'placeholder': 'e.g. Shop 12, Market Complex'
        })
    )

    # Owner account details
    owner_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs',
            'placeholder': 'e.g. royalpunjab'
        })
    )
    owner_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs',
            'placeholder': 'owner@example.com'
        })
    )
    owner_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs',
            'placeholder': 'Set initial password'
        })
    )

    # Subscription settings
    trial_days = forms.IntegerField(
        initial=14,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs'
        })
    )
    initial_plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs'
        })
    )

    def clean_slug(self):
        slug = self.cleaned_data['slug'].lower().strip()
        if Restaurant.objects.filter(slug=slug).exists():
            raise forms.ValidationError('A restaurant with this slug already exists.')
        return slug

    def clean_owner_username(self):
        username = self.cleaned_data['owner_username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with this username already exists.')
        return username

    def clean_owner_email(self):
        email = self.cleaned_data['owner_email'].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class SubscriptionEditForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['plan', 'status', 'trial_end', 'current_period_end', 'auto_renew']
        widgets = {
            'plan': forms.Select(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs'
            }),
            'trial_end': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs'
            }),
            'current_period_end': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full text-xs rounded-xl px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 transition-all shadow-xs'
            }),
        }


class RestaurantEditForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'slug', 'whatsapp_number', 'number_of_tables', 'address', 'google_review_url', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'w-full text-xs font-mono rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
            }),
            'number_of_tables': forms.NumberInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
            }),
            'google_review_url': forms.URLInput(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full text-xs rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
            }),
        }

    def clean_slug(self):
        slug = self.cleaned_data['slug'].lower().strip()
        qs = Restaurant.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A restaurant with this slug already exists.')
        return slug


class OwnerAccountEditForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs'
        })
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full text-xs rounded-xl px-3.5 py-2 bg-white border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-600 shadow-xs',
            'placeholder': 'Leave blank to keep unchanged'
        }),
        help_text='Enter a new password if you want to reset the owner login.'
    )
