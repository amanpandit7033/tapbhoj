import re
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from restaurants.models import Restaurant
from menu.models import MenuItem
from orders.models import TableSession, TableCartItem


class TableCartConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer managing real-time collaborative group carts.
    Multiple diners at the same table join the same room group and see
    real-time cart updates instantly.
    """

    async def connect(self):
        self.restaurant_slug = self.scope['url_route']['kwargs']['slug']
        raw_table = self.scope['url_route']['kwargs']['table_number']
        self.table_number = re.sub(r'[^a-zA-Z0-9_\-]', '', str(raw_table).strip())

        # Verify restaurant exists
        self.restaurant = await self.get_restaurant(self.restaurant_slug)
        if not self.restaurant or not self.table_number:
            await self.close()
            return

        # Room group name per table per restaurant
        self.room_group_name = f"cart_{self.restaurant_slug}_{self.table_number}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial cart state to the freshly connected diner
        session = await self.get_or_create_table_session()
        cart_payload = await self.get_cart_payload(session)
        await self.send_json({
            'type': 'cart_init',
            'table_number': self.table_number,
            'cart': cart_payload,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content):
        action = content.get('action')
        diner_name = content.get('diner_name', 'Someone')

        if action == 'update_item':
            menu_item_id = content.get('item_id')
            delta = int(content.get('delta', 1))

            session = await self.get_or_create_table_session()
            result = await self.apply_item_delta(session, menu_item_id, delta, diner_name)
            if result:
                cart_payload, item_name, new_qty = result
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cart_broadcast',
                        'cart': cart_payload,
                        'actor': diner_name,
                        'message': f"{diner_name} {'added' if delta > 0 else 'removed'} {item_name}",
                        'item_id': menu_item_id,
                    }
                )

        elif action == 'rename_diner':
            old_name = content.get('old_name')
            new_name = content.get('new_name')
            if old_name and new_name and old_name != new_name:
                session = await self.get_or_create_table_session()
                cart_payload = await self.rename_diner_items(session, old_name, new_name)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cart_broadcast',
                        'cart': cart_payload,
                        'actor': new_name,
                        'message': f"{old_name} is now {new_name}",
                    }
                )

        elif action == 'clear_cart':
            session = await self.get_or_create_table_session()
            await self.clear_session_cart(session)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'cart_broadcast',
                    'cart': {},
                    'actor': diner_name,
                    'message': f"{diner_name} cleared the cart",
                }
            )

    async def cart_broadcast(self, event):
        """Dispatches group updates to the connected WebSocket client."""
        await self.send_json(event)

    async def order_redirect_broadcast(self, event):
        """Notifies all connected table devices to redirect to order tracking."""
        await self.send_json(event)

    async def table_cleared_broadcast(self, event):
        """Notifies all connected table devices when cashier clears the table."""
        await self.send_json(event)

    # Database Helpers
    @database_sync_to_async
    def get_restaurant(self, slug):
        return Restaurant.objects.filter(slug=slug, status='active').first()

    @database_sync_to_async
    def get_or_create_table_session(self):
        session, _ = TableSession.objects.get_or_create(
            restaurant=self.restaurant,
            table_number=self.table_number,
            is_active=True
        )
        return session

    @database_sync_to_async
    def get_cart_payload(self, session):
        return session.get_cart_payload()

    @database_sync_to_async
    def apply_item_delta(self, session, item_id, delta, diner_name):
        menu_item = MenuItem.objects.filter(
            id=item_id,
            category__restaurant=self.restaurant,
            is_available=True
        ).first()
        if not menu_item:
            return None

        cart_item, created = TableCartItem.objects.get_or_create(
            session=session,
            menu_item=menu_item,
            defaults={'quantity': max(1, delta), 'added_by': diner_name}
        )

        if not created:
            new_qty = cart_item.quantity + delta
            if new_qty <= 0:
                cart_item.delete()
                new_qty = 0
            else:
                cart_item.quantity = new_qty
                cart_item.added_by = diner_name
                cart_item.save(update_fields=['quantity', 'added_by', 'updated_at'])
        else:
            new_qty = cart_item.quantity

        return session.get_cart_payload(), menu_item.name, new_qty

    @database_sync_to_async
    def clear_session_cart(self, session):
        session.cart_items.all().delete()

    @database_sync_to_async
    def rename_diner_items(self, session, old_name, new_name):
        session.cart_items.filter(added_by=old_name).update(added_by=new_name)
        return session.get_cart_payload()


class RestaurantOrdersConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for restaurant dashboard.
    Receives real-time push notifications when customers place an order
    or update payment status at their tables.
    """
    async def connect(self):
        self.restaurant_slug = self.scope['url_route']['kwargs']['slug']
        self.room_group_name = f"restaurant_orders_{self.restaurant_slug}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def new_order_event(self, event):
        """Pushes new order alert to connected dashboard."""
        await self.send_json(event)

    async def payment_update_event(self, event):
        """Pushes payment status changes to connected dashboard."""
        await self.send_json(event)


