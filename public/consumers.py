import re
import urllib.parse
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from restaurants.models import Restaurant
from menu.models import MenuItem
from orders.models import TableSession, TableCartItem

CONNECTED_TABLE_DINERS = {}


def get_table_diners(slug, table_number):
    """Returns list of distinct active diner names currently connected at this table."""
    table_key = (slug, str(table_number).strip())
    conns = CONNECTED_TABLE_DINERS.get(table_key, {})
    names = []
    for d in conns.values():
        name = (d or '').strip()
        if name and name not in names:
            names.append(name)
    return names


class TableCartConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer managing real-time collaborative group carts and table presence.
    Multiple diners at the same table join the same room group, see live presence of fellow diners,
    and see real-time cart updates instantly.
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

        # Parse diner_name from query parameters if present
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        params = urllib.parse.parse_qs(query_string)
        raw_diner = params.get('diner', [''])[0].strip()
        self.diner_name = raw_diner or 'Guest'

        # Room group name per table per restaurant
        self.room_group_name = f"cart_{self.restaurant_slug}_{self.table_number}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Track connection in presence map
        table_key = (self.restaurant_slug, self.table_number)
        if table_key not in CONNECTED_TABLE_DINERS:
            CONNECTED_TABLE_DINERS[table_key] = {}
        CONNECTED_TABLE_DINERS[table_key][self.channel_name] = self.diner_name

        # Send initial cart & presence state to the freshly connected diner
        session = await self.get_or_create_table_session()
        live_diners = get_table_diners(self.restaurant_slug, self.table_number)
        await self.save_session_diners(session, live_diners)

        cart_payload = await self.get_cart_payload(session)
        await self.send_json({
            'type': 'cart_init',
            'table_number': self.table_number,
            'cart': cart_payload,
            'diners': live_diners,
            'count': len(live_diners),
        })

        # Broadcast live table presence to dashboard
        try:
            await self.channel_layer.group_send(
                f"restaurant_orders_{self.restaurant_slug}",
                {
                    'type': 'table_presence_event',
                    'table_number': self.table_number,
                    'diners': live_diners,
                    'count': len(live_diners),
                }
            )
        except Exception:
            pass

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        table_key = (getattr(self, 'restaurant_slug', ''), getattr(self, 'table_number', ''))
        if table_key in CONNECTED_TABLE_DINERS:
            CONNECTED_TABLE_DINERS[table_key].pop(self.channel_name, None)
            if not CONNECTED_TABLE_DINERS[table_key]:
                CONNECTED_TABLE_DINERS.pop(table_key, None)

        if hasattr(self, 'restaurant_slug') and hasattr(self, 'table_number'):
            live_diners = get_table_diners(self.restaurant_slug, self.table_number)
            try:
                session = await self.get_or_create_table_session()
                await self.save_session_diners(session, live_diners)
                await self.broadcast_presence(live_diners)
            except Exception:
                pass

    async def receive_json(self, content):
        action = content.get('action')
        diner_name = content.get('diner_name', 'Someone')

        if action == 'join_table':
            new_name = content.get('diner_name', '').strip()
            if new_name:
                self.diner_name = new_name
                table_key = (self.restaurant_slug, self.table_number)
                if table_key not in CONNECTED_TABLE_DINERS:
                    CONNECTED_TABLE_DINERS[table_key] = {}
                CONNECTED_TABLE_DINERS[table_key][self.channel_name] = self.diner_name

                live_diners = get_table_diners(self.restaurant_slug, self.table_number)
                session = await self.get_or_create_table_session()
                await self.save_session_diners(session, live_diners)
                await self.broadcast_presence(live_diners)

        elif action == 'update_item':
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
                self.diner_name = new_name
                table_key = (self.restaurant_slug, self.table_number)
                if table_key not in CONNECTED_TABLE_DINERS:
                    CONNECTED_TABLE_DINERS[table_key] = {}
                CONNECTED_TABLE_DINERS[table_key][self.channel_name] = self.diner_name

                session = await self.get_or_create_table_session()
                cart_payload = await self.rename_diner_items(session, old_name, new_name)
                live_diners = get_table_diners(self.restaurant_slug, self.table_number)
                await self.save_session_diners(session, live_diners)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cart_broadcast',
                        'cart': cart_payload,
                        'actor': new_name,
                        'message': f"{old_name} is now {new_name}",
                    }
                )
                await self.broadcast_presence(live_diners)

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

    async def broadcast_presence(self, live_diners):
        """Broadcasts live presence of seated diners to table room and restaurant dashboard."""
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_broadcast',
                    'table_number': self.table_number,
                    'diners': live_diners,
                    'count': len(live_diners),
                }
            )
            await self.channel_layer.group_send(
                f"restaurant_orders_{self.restaurant_slug}",
                {
                    'type': 'table_presence_event',
                    'table_number': self.table_number,
                    'diners': live_diners,
                    'count': len(live_diners),
                }
            )
        except Exception:
            pass

    async def presence_broadcast(self, event):
        """Dispatches table presence list & count to connected table diner."""
        await self.send_json(event)

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

    @database_sync_to_async
    def save_session_diners(self, session, diners):
        if session:
            session.active_diners = diners
            session.save(update_fields=['active_diners', 'updated_at'])


class RestaurantOrdersConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for restaurant dashboard.
    Receives real-time push notifications when customers place an order,
    update payment status, or join/leave tables.
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

    async def table_presence_event(self, event):
        """Pushes live table presence updates (persons count and names) to store dashboard."""
        await self.send_json(event)



