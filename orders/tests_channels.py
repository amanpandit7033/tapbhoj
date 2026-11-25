import json
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from channels.testing import WebsocketCommunicator
from config.asgi import application
from restaurants.models import Restaurant
from menu.models import Category, MenuItem
from orders.models import TableSession, TableCartItem


class TableSessionModelTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Palace',
            slug='test-palace',
            whatsapp_number='919999999999',
            status='active'
        )
        self.category = Category.objects.create(
            restaurant=self.restaurant,
            name='Mains',
            position=1
        )
        self.item1 = MenuItem.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name='Paneer Butter Masala',
            price=Decimal('250.00'),
            is_available=True,
            is_veg=True
        )

    def test_table_session_creation_and_payload(self):
        session = TableSession.objects.create(
            restaurant=self.restaurant,
            table_number='5'
        )
        self.assertTrue(session.is_active)
        self.assertEqual(session.get_cart_payload(), {})

        cart_item = TableCartItem.objects.create(
            session=session,
            menu_item=self.item1,
            quantity=2,
            added_by='Rahul'
        )
        payload = session.get_cart_payload()
        self.assertIn(str(self.item1.id), payload)
        self.assertEqual(payload[str(self.item1.id)]['name'], 'Paneer Butter Masala')
        self.assertEqual(payload[str(self.item1.id)]['quantity'], 2)
        self.assertEqual(payload[str(self.item1.id)]['added_by'], 'Rahul')


class TableCartConsumerTests(TransactionTestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Taj Cafe',
            slug='taj-cafe',
            whatsapp_number='919876543200',
            status='active'
        )
        self.category = Category.objects.create(
            restaurant=self.restaurant,
            name='Starters',
            position=1
        )
        self.dish = MenuItem.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name='Crispy Corn',
            price=Decimal('180.00'),
            is_available=True,
            is_veg=True
        )

    async def test_websocket_connect_and_cart_sync(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/table/taj-cafe/3/cart/"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # First message is cart_init
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'cart_init')
        self.assertEqual(response['table_number'], '3')
        self.assertEqual(response['cart'], {})

        # Diner A adds 1 Crispy Corn
        await communicator.send_json_to({
            'action': 'update_item',
            'item_id': self.dish.id,
            'delta': 1,
            'diner_name': 'Amit'
        })

        broadcast = await communicator.receive_json_from()
        self.assertEqual(broadcast['type'], 'cart_broadcast')
        self.assertIn(str(self.dish.id), broadcast['cart'])
        self.assertEqual(broadcast['cart'][str(self.dish.id)]['quantity'], 1)
        self.assertEqual(broadcast['actor'], 'Amit')
        self.assertIn('Amit added Crispy Corn', broadcast['message'])

        # Clear cart action
        await communicator.send_json_to({
            'action': 'clear_cart',
            'diner_name': 'Amit'
        })

        broadcast_clear = await communicator.receive_json_from()
        self.assertEqual(broadcast_clear['type'], 'cart_broadcast')
        self.assertEqual(broadcast_clear['cart'], {})

        await communicator.disconnect()

    async def test_websocket_rename_diner_retroactive_attribution(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/table/taj-cafe/7/cart/"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()  # cart_init

        # 1. User adds item as 'Guest 888'
        await communicator.send_json_to({
            'action': 'update_item',
            'item_id': self.dish.id,
            'delta': 1,
            'diner_name': 'Guest 888'
        })
        b1 = await communicator.receive_json_from()
        self.assertEqual(b1['cart'][str(self.dish.id)]['added_by'], 'Guest 888')

        # 2. User customizes their name to 'Aman'
        await communicator.send_json_to({
            'action': 'rename_diner',
            'old_name': 'Guest 888',
            'new_name': 'Aman'
        })
        b2 = await communicator.receive_json_from()
        self.assertEqual(b2['type'], 'cart_broadcast')
        # Previously added item now shows 'Aman'
        self.assertEqual(b2['cart'][str(self.dish.id)]['added_by'], 'Aman')
        self.assertIn('Guest 888 is now Aman', b2['message'])

        await communicator.disconnect()

