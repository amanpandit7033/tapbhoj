from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from restaurants.models import Restaurant
from accounts.models import OwnerProfile


class RootRedirectTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        """Unauthenticated visitor to root / redirects to login page."""
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('login'))

    def test_owner_redirects_to_dashboard(self):
        """Authenticated restaurant owner redirects to dashboard:home."""
        restaurant = Restaurant.objects.create(
            name='Test Cafe',
            slug='test-cafe',
            whatsapp_number='919876543210'
        )
        user = User.objects.create_user(username='owner1', password='Password@123')
        OwnerProfile.objects.create(user=user, restaurant=restaurant)
        self.client.login(username='owner1', password='Password@123')

        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('dashboard:home'))

    def test_admin_redirects_to_platform(self):
        """Authenticated superuser redirects to platform:dashboard."""
        User.objects.create_superuser(username='admin', password='Password@123', email='admin@tapbhoj.in')
        self.client.login(username='admin', password='Password@123')

        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('platform:dashboard'))
