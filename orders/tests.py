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
        """Diners can send order data with a valid signed table_token to log_order."""
        from restaurants.utils import encode_table_token
        url = reverse('public:log_order', kwargs={'slug': 'rasoi-a'})
        payload = {
            'table_token': encode_table_token(self.restaurant_a, '7'),
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

    def test_public_log_order_rejects_forged_or_missing_token(self):
        """Orders without a valid signed table_token must be rejected with 403."""
        url = reverse('public:log_order', kwargs={'slug': 'rasoi-a'})
        res = self.client.post(
            url,
            data=json.dumps({
                'table_number': '7',
                'table_token': 'tampered-token',
                'items': [{'name': 'Paneer Tikka', 'price': 260.0, 'quantity': 1}],
                'total_amount': '260.00',
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json().get('code'), 'INVALID_TABLE_URL')

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

    def test_free_direct_upi_flow_and_cashier_verification(self):
        """End-to-end Free Direct UPI payment flow, UTR submission, cashier verification, and receipt."""
        # 1. Diner creates order with UPI pending
        from restaurants.utils import encode_table_token
        url_log = reverse('public:log_order', kwargs={'slug': 'rasoi-a'})
        log_res = self.client.post(
            url_log,
            data=json.dumps({
                'table_token': encode_table_token(self.restaurant_a, '4'),
                'table_number': '4',
                'items': [{'id': 1, 'name': 'Dal Makhani', 'price': 280.0, 'quantity': 1, 'item_total': 280.0}],
                'total_amount': '280.00',
                'payment_method': 'upi',
                'payment_status': 'pending'
            }),
            content_type='application/json'
        )
        self.assertEqual(log_res.status_code, 200)
        order_id = log_res.json()['order_id']

        # 2. Diner submits UTR
        url_utr = reverse('public:submit_upi_payment', kwargs={'slug': 'rasoi-a'})
        utr_res = self.client.post(
            url_utr,
            data=json.dumps({'order_id': order_id, 'upi_utr': '987654321012'}),
            content_type='application/json'
        )
        self.assertEqual(utr_res.status_code, 200)

        # 3. Diner client polls status -> still pending
        url_status = reverse('public:payment_status', kwargs={'slug': 'rasoi-a', 'order_id': order_id})
        status_res = self.client.get(url_status)
        self.assertFalse(status_res.json()['is_paid'])
        self.assertEqual(status_res.json()['payment_status'], 'pending')

        # 4. Cashier logs in and confirms payment
        self.client.login(username='owner_a', password='Password@123')
        url_confirm = reverse('dashboard:order_payment_status', kwargs={'pk': order_id})
        confirm_res = self.client.post(url_confirm, {'payment_status': 'paid'})
        self.assertEqual(confirm_res.status_code, 302)

        # 5. Diner client polls status again -> now paid with receipt URL
        status_res2 = self.client.get(url_status)
        self.assertTrue(status_res2.json()['is_paid'])
        self.assertEqual(status_res2.json()['payment_status'], 'paid')
        receipt_url = status_res2.json()['receipt_url']

        # 6. Verify digital e-receipt page renders cleanly
        receipt_page = self.client.get(receipt_url)
        self.assertEqual(receipt_page.status_code, 200)
        self.assertContains(receipt_page, 'Rasoi A')
        self.assertContains(receipt_page, 'Table 4')
        self.assertContains(receipt_page, '280')

    def test_owner_cannot_verify_other_restaurant_payment(self):
        """Owner A cannot approve or modify payment status for Restaurant B's order."""
        self.client.login(username='owner_a', password='Password@123')
        url = reverse('dashboard:order_payment_status', kwargs={'pk': self.order_b.pk})
        response = self.client.post(url, {'payment_status': 'paid'})
        self.assertEqual(response.status_code, 404)

