from django import forms
from django.contrib.auth.models import User
from restaurants.models import Restaurant
from .models import Plan, Subscription


class RestaurantOnboardForm(forms.Form):
    # Restaurant details
    restaurant_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
            'placeholder': 'e.g. Royal Punjab Dhaba'
        })
    )
    slug = forms.SlugField(
        max_length=150,
        help_text='Unique URL identifier: tapbhoj.in/r/<slug>/',
        widget=forms.TextInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
            'placeholder': 'royal-punjab-dhaba'
        })
    )
    whatsapp_number = forms.CharField(
        max_length=20,
        help_text='With country code, no + or spaces (e.g. 919876543210)',
        widget=forms.TextInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
            'placeholder': '919876543210'
        })
    )
    number_of_tables = forms.IntegerField(
        initial=10,
        min_value=1,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
            'placeholder': 'e.g. Shop 12, Market Complex'
        })
    )

    # Owner account details
    owner_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
            'placeholder': 'e.g. royalpunjab'
        })
    )
    owner_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
            'placeholder': 'owner@example.com'
        })
    )
    owner_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none',
            'placeholder': 'Set initial password'
        })
    )

    # Subscription settings
    trial_days = forms.IntegerField(
        initial=14,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none'
        })
    )
    initial_plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark focus:ring-2 focus:ring-tapbhoj-brand dark:focus:ring-tapbhoj-accent focus:outline-none'
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
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark'
            }),
            'trial_end': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark'
            }),
            'current_period_end': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full text-sm rounded-xl px-3.5 py-2.5 bg-tapbhoj-surface dark:bg-tapbhoj-surface-dark border border-black/10 dark:border-white/10 text-tapbhoj-ink dark:text-tapbhoj-ink-dark'
            }),
        }
