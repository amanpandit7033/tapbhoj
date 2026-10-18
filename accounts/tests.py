from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from accounts.models import OwnerProfile
from restaurants.models import Restaurant
from menu.models import Category, MenuItem


class TenantIsolationAndDashboardTests(TestCase):
    def setUp(self):
        # Restaurant A and Owner A
        self.restaurant_a = Restaurant.objects.create(
            name='Restaurant A',
            slug='restaurant-a',
            whatsapp_number='919876543210',
            status='active',
            number_of_tables=5
        )
        self.user_a = User.objects.create_user(
            username='user_a', password='Password@123'
        )
        self.profile_a = OwnerProfile.objects.create(
            user=self.user_a, restaurant=self.restaurant_a
        )

        # Restaurant B and Owner B
        self.restaurant_b = Restaurant.objects.create(
            name='Restaurant B',
            slug='restaurant-b',
            whatsapp_number='919876543219',
            status='active',
            number_of_tables=10
        )
        self.user_b = User.objects.create_user(
            username='user_b', password='Password@123'
        )
        self.profile_b = OwnerProfile.objects.create(
            user=self.user_b, restaurant=self.restaurant_b
        )

        # Categories & items for Restaurant A
        self.cat_a = Category.objects.create(
            restaurant=self.restaurant_a, name='Mains A', position=1
        )
        self.item_a = MenuItem.objects.create(
            restaurant=self.restaurant_a, category=self.cat_a,
            name='Dish A', price=Decimal('100.00'), is_available=True
        )

        # Categories & items for Restaurant B
        self.cat_b = Category.objects.create(
            restaurant=self.restaurant_b, name='Mains B', position=1
        )
        self.item_b = MenuItem.objects.create(
            restaurant=self.restaurant_b, category=self.cat_b,
            name='Dish B', price=Decimal('200.00'), is_available=True
        )

    def test_unauthenticated_dashboard_redirects_to_login(self):
        """Unauthenticated user accessing /dashboard/ must be redirected to /login/."""
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_owner_a_dashboard_shows_only_restaurant_a(self):
        """Owner A logged in must see Restaurant A data, never Restaurant B."""
        self.client.login(username='user_a', password='Password@123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Restaurant A')
        self.assertNotContains(response, 'Restaurant B')

    def test_owner_a_menu_shows_only_restaurant_a_items(self):
        """Menu manager must only list items belonging to the logged-in owner's restaurant."""
        self.client.login(username='user_a', password='Password@123')
        response = self.client.get(reverse('dashboard:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dish A')
        self.assertNotContains(response, 'Dish B')

    def test_owner_a_cannot_edit_owner_b_item(self):
        """Multi-tenant security: Owner A attempting to edit Owner B's item must 404."""
        self.client.login(username='user_a', password='Password@123')
        edit_url = reverse('dashboard:item_edit', kwargs={'pk': self.item_b.pk})
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 404)

    def test_owner_a_cannot_delete_owner_b_category(self):
        """Multi-tenant security: Owner A attempting to delete Owner B's category must 404."""
        self.client.login(username='user_a', password='Password@123')
        delete_url = reverse('dashboard:category_delete', kwargs={'pk': self.cat_b.pk})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 404)
        # Verify category B was NOT deleted
        self.assertTrue(Category.objects.filter(pk=self.cat_b.pk).exists())

    def test_one_tap_sold_out_toggle(self):
        """Owner can toggle an item between available and sold out with one tap."""
        self.client.login(username='user_a', password='Password@123')
        toggle_url = reverse('dashboard:item_toggle', kwargs={'pk': self.item_a.pk})

        # Toggle to sold out
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 302)
        self.item_a.refresh_from_db()
        self.assertFalse(self.item_a.is_available)

        # Toggle back to available
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 302)
        self.item_a.refresh_from_db()
        self.assertTrue(self.item_a.is_available)

    def test_owner_a_cannot_toggle_owner_b_item(self):
        """Owner A attempting to toggle availability of Owner B's item must 404."""
        self.client.login(username='user_a', password='Password@123')
        toggle_url = reverse('dashboard:item_toggle', kwargs={'pk': self.item_b.pk})
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 404)
        # Verify item B status unchanged
        self.item_b.refresh_from_db()
        self.assertTrue(self.item_b.is_available)

    def test_qr_code_endpoint_returns_png(self):
        """Table QR code endpoint must return a valid image/png."""
        self.client.login(username='user_a', password='Password@123')
        qr_url = reverse('dashboard:table_qr', kwargs={'table_number': 3})
        response = self.client.get(qr_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(len(response.content) > 100)
