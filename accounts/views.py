from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.urls import reverse


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    """Allows logging in with either username or email (case-insensitive)."""
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            username_cleaned = username.strip()
            # If user typed an email address
            if '@' in username_cleaned:
                try:
                    user_match = User.objects.filter(email__iexact=username_cleaned).first()
                    if user_match:
                        username_cleaned = user_match.username
                except Exception:
                    pass
            else:
                try:
                    user_match = User.objects.filter(username__iexact=username_cleaned).first()
                    if user_match:
                        username_cleaned = user_match.username
                except Exception:
                    pass

            self.user_cache = authenticate(self.request, username=username_cleaned, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class TapBhojLoginView(LoginView):
    """Custom login view with smart redirection based on user role."""
    template_name = 'accounts/login.html'
    form_class = EmailOrUsernameAuthenticationForm

    def get_default_redirect_url(self):
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            return reverse('platform:dashboard')
        from core.decorators import get_store_role
        role, _ = get_store_role(self.request.user)
        if role in ('cashier', 'waiter', 'kitchen'):
            return reverse('dashboard:orders')
        return reverse('dashboard:home')
