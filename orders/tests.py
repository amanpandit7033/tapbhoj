import json
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from accounts.models import OwnerProfile
from restaurants.models import Restaurant
from .models import OrderLog


class OrdersAndInsightsTests(TestCase):
    def setUp(self):
        # Restaurant A and Owner A
        self.restaurant_a = Restaurant.objects.create(
            name='Rasoi A',
            slug='rasoi-a',
            whatsapp_number='919876543210',
            status='active',
            number_of_tables=10
        )
        self.owner_a = User.objects.create_user(
            username='owner_a', password='Password@123'
        )
        self.profile_a = OwnerProfile.objects.create(
            user=self.owner_a, restaurant=self.restaurant_a
        )

        # Restaurant B and Owner B
        self.restaurant_b = Restaurant.objects.create(
            name='Rasoi B',
            slug='rasoi-b',
            whatsapp_number='919876543219',
            status='active',
            number_of_tables=10
        )
        self.owner_b = User.objects.create_user(
            username='owner_b', password='Password@123'
        )
        self.profile_b = OwnerProfile.objects.create(
            user=self.owner_b, restaurant=self.restaurant_b
        )

        # Seed orders for Restaurant A
        self.order_a = OrderLog.objects.create(
            restaurant=self.restaurant_a,
            table_number='3',
            items_json=[
                {'id': 1, 'name': 'Dal Makhani', 'price': 280.0, 'quantity': 2, 'item_total': 560.0, 'is_veg': True},
                {'id': 2, 'name': 'Butter Naan', 'price': 55.0, 'quantity': 3, 'item_total': 165.0, 'is_veg': True},
            ],
            total_amount=Decimal('725.00'),
            customer_note='Extra butter please',
            status='sent'
        )

        # Seed orders for Restaurant B
        self.order_b = OrderLog.objects.create(
            restaurant=self.restaurant_b,
            table_number='5',
            items_json=[
                {'id': 10, 'name': 'Biryani B', 'price': 350.0, 'quantity': 1, 'item_total': 350.0, 'is_veg': False},
            ],
            total_amount=Decimal('350.00'),
            status='sent'
        )

    def test_public_log_order_endpoint(self):
        """Diners can send order data to log_order endpoint and create an OrderLog entry."""
        url = reverse('public:log_order', kwargs={'slug': 'rasoi-a'})
        payload = {
            'table_number': '7',
            'items': [
                {'name': 'Paneer Tikka', 'price': 260.0, 'quantity': 1, 'item_total': 260.0, 'is_veg': True}
            ],
            'total_amount': '260.00',
            'customer_note': 'Mild spicy'
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')

        # Verify recorded in DB
        created_order = OrderLog.objects.get(id=data['order_id'])
        self.assertEqual(created_order.restaurant, self.restaurant_a)
        self.assertEqual(created_order.table_number, '7')
        self.assertEqual(created_order.total_amount, Decimal('260.00'))
        self.assertEqual(created_order.customer_note, 'Mild spicy')

    def test_owner_orders_tenant_isolation(self):
        """Owner A dashboard must only show Restaurant A orders, never Restaurant B."""
        self.client.login(username='owner_a', password='Password@123')
        url = reverse('dashboard:orders')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/orders.html')
        self.assertContains(response, 'Dal Makhani')
        self.assertContains(response, 'Table 3')
        self.assertNotContains(response, 'Biryani B')

    def test_order_status_update(self):
        """Owner can update the status of their order."""
        self.client.login(username='owner_a', password='Password@123')
        url = reverse('dashboard:order_status', kwargs={'pk': self.order_a.pk})

        response = self.client.post(url, {'status': 'completed'})
        self.assertEqual(response.status_code, 302)

        self.order_a.refresh_from_db()
        self.assertEqual(self.order_a.status, 'completed')

    def test_owner_cannot_update_other_restaurant_order(self):
        """Owner A cannot update order belonging to Restaurant B (must 404)."""
        self.client.login(username='owner_a', password='Password@123')
        url = reverse('dashboard:order_status', kwargs={'pk': self.order_b.pk})

        response = self.client.post(url, {'status': 'completed'})
        self.assertEqual(response.status_code, 404)

        self.order_b.refresh_from_db()
        self.assertEqual(self.order_b.status, 'sent')

    def test_popular_dishes_aggregation(self):
        """Verify popular dishes calculation in context."""
        self.client.login(username='owner_a', password='Password@123')
        response = self.client.get(reverse('dashboard:orders') + '?range=all')
        self.assertEqual(response.status_code, 200)

        popular = response.context['popular_dishes']
        self.assertTrue(len(popular) > 0)
        # Butter Naan had qty 3, Dal Makhani had qty 2
        dish_names = [d['name'] for d in popular]
        self.assertIn('Butter Naan', dish_names)
        self.assertIn('Dal Makhani', dish_names)
        self.assertEqual(popular[0]['name'], 'Butter Naan')
        self.assertEqual(popular[0]['count'], 3)
