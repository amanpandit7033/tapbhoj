import json
from decimal import Decimal
from django.db import models
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from restaurants.models import Restaurant
from menu.models import Category
from orders.models import OrderLog


def restaurant_menu(request, slug):
    """
    Public menu view for a restaurant.
    Renders the live menu if active, or a paused notice if inactive.
    Pre-fills table number from URL parameter `?table=N`.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)

    # Check if restaurant is temporarily unavailable/paused (Requirement C9)
    if not restaurant.is_live:
        return render(request, 'public/paused.html', {
            'restaurant': restaurant
        }, status=503)

    # Pre-fill table number from query parameter (Requirement C2)
    table_number = request.GET.get('table', '').strip()

    # If this table already has an order where bill has been requested or payment is pending/paid,
    # redirect directly to the tracking/payment screen to prevent ordering on a finalized bill!
    cookie_session_token = request.COOKIES.get(f"tbl_token_{restaurant.slug}_{table_number}")
    session_obj = None

    if table_number:
        import re, secrets
        from orders.models import TableSession
        clean_table = re.sub(r'[^a-zA-Z0-9_\-]', '', table_number)
        active_session = TableSession.objects.filter(
            restaurant=restaurant,
            table_number=clean_table,
            is_active=True
        ).first()

        # If no active session exists, start a fresh session with a unique token
        if not active_session:
            new_token = secrets.token_urlsafe(16)
            active_session = TableSession.objects.create(
                restaurant=restaurant,
                table_number=clean_table,
                session_token=new_token,
                is_active=True
            )
        elif not active_session.session_token:
            active_session.session_token = secrets.token_urlsafe(16)
            active_session.save(update_fields=['session_token'])

        session_obj = active_session

        if active_session:
            settling_order = active_session.orders.filter(
                models.Q(payment_requested=True) | models.Q(payment_status__in=['pending', 'paid'])
            ).exclude(status='cancelled').order_by('-created_at').first()

            if settling_order:
                if settling_order.payment_status == 'paid':
                    return redirect('public:receipt', slug=restaurant.slug, order_id=settling_order.id)
                else:
                    return redirect('public:order_tracking', slug=restaurant.slug, order_id=settling_order.id)

    # Fetch visible categories with pre-fetched menu items ordered by position (Requirement C3, Performance)
    categories = restaurant.categories.filter(is_visible=True).prefetch_related('items')

    context = {
        'restaurant': restaurant,
        'categories': categories,
        'table_number': table_number,
    }
    response = render(request, 'public/menu.html', context)
    if session_obj and session_obj.session_token:
        # Save session token in client cookie so subsequent orders must match this physical table session
        response.set_cookie(
            f"tbl_token_{restaurant.slug}_{table_number}",
            session_obj.session_token,
            max_age=12 * 3600,
            httponly=True,
            samesite='Lax'
        )
    return response


@require_POST
def log_public_order(request, slug):
    """
    Phase 4: Logs the order in the database when the customer taps "Send order on WhatsApp".
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)
    
    if not restaurant.is_live:
        return HttpResponseBadRequest("Restaurant is not accepting orders.")

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON data.")

    table_number = str(data.get('table_number', '')).strip()
    items = data.get('items', [])
    total_amount = Decimal(str(data.get('total_amount', '0.00')))
    customer_note = str(data.get('customer_note', '')).strip()

    if not table_number:
        return HttpResponseBadRequest("Table number is required.")

    # Geofence Validation: Circular Radius from Restaurant Coordinates
    has_geofence = bool(restaurant.latitude is not None and restaurant.longitude is not None)

    if has_geofence:
        client_lat = data.get('lat')
        client_lng = data.get('lng')

        if client_lat is not None and client_lng is not None:
            try:
                cl_lat = float(client_lat)
                cl_lng = float(client_lng)

                import math
                lat1, lon1 = math.radians(float(restaurant.latitude)), math.radians(float(restaurant.longitude))
                lat2, lon2 = math.radians(cl_lat), math.radians(cl_lng)

                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                distance_meters = 6371000 * c  # Earth radius in meters

                allowed_radius = restaurant.geofence_radius or 100
                if distance_meters > allowed_radius:
                    return JsonResponse({
                        'status': 'error',
                        'code': 'OUT_OF_RANGE',
                        'message': f"You appear to be {distance_meters:.0f}m away from the restaurant. Ordering is only permitted within {allowed_radius}m of {restaurant.name}.",
                    }, status=403)
            except Exception:
                pass
        else:
            # Coordinates missing when required by restaurant geofencing
            return JsonResponse({
                'status': 'error',
                'code': 'LOCATION_REQUIRED',
                'message': 'Please allow location access on your phone to verify you are seated at the restaurant.',
            }, status=403)

    # Link to or start active dining TableSession
    import re, secrets
    from orders.models import TableSession
    clean_table = re.sub(r'[^a-zA-Z0-9_\-]', '', table_number)

    # Check for active table session
    active_session = TableSession.objects.filter(
        restaurant=restaurant,
        table_number=clean_table,
        is_active=True
    ).first()

    cookie_token = request.COOKIES.get(f"tbl_token_{restaurant.slug}_{table_number}")

    # Security check: If a session is active and has a token, ensure the client holds the active token
    # or starts a fresh table session only if no current session is ongoing
    if active_session:
        session = active_session
        if active_session.session_token and cookie_token and cookie_token != active_session.session_token:
            # Token mismatch: Customer tab belongs to an old or cleared dining session!
            return JsonResponse({
                'status': 'error',
                'code': 'SESSION_EXPIRED',
                'message': 'Your dining session for this table has expired or was cleared by the cashier. Please scan the QR code on your table to begin a fresh order.',
            }, status=403)
    else:
        # Create fresh session
        session = TableSession.objects.create(
            restaurant=restaurant,
            table_number=clean_table,
            session_token=secrets.token_urlsafe(16),
            is_active=True
        )

    payment_method = str(data.get('payment_method', 'upi_direct')).strip()
    payment_status = str(data.get('payment_status', 'unpaid')).strip()
    if payment_status not in dict(OrderLog.PAYMENT_STATUS_CHOICES):
        payment_status = 'unpaid'

    # Check if a bill has already been requested or paid for this table
    existing_order = OrderLog.objects.filter(
        restaurant=restaurant,
        session=session,
    ).exclude(status__in=['completed', 'cancelled']).order_by('-created_at').first()

    # Rule 1: If bill was already requested (payment_requested=True or payment_status in ['pending', 'paid']),
    # lock the menu from adding new items and redirect diner back to the tracking/payment screen!
    if existing_order and (existing_order.payment_requested or existing_order.payment_status in ['pending', 'paid']):
        tracking_url = reverse('public:order_tracking', kwargs={'slug': restaurant.slug, 'order_id': existing_order.id})
        return JsonResponse({
            'status': 'error',
            'code': 'BILL_ALREADY_REQUESTED',
            'message': 'The bill for this table is already being finalized or paid. Please settle the current bill with your server before placing new orders.',
            'tracking_url': tracking_url,
        }, status=400)

    if existing_order and existing_order.payment_status == 'unpaid':
        # Merge new items into existing order!
        merged_items = list(existing_order.items_json or [])
        for new_item in items:
            # Check if item already exists with same id to increase quantity
            matched = False
            for existing_item in merged_items:
                if str(existing_item.get('id')) == str(new_item.get('id')):
                    existing_item['quantity'] = int(existing_item.get('quantity', 1)) + int(new_item.get('quantity', 1))
                    existing_item['item_total'] = float(existing_item['quantity']) * float(existing_item.get('price', 0))
                    matched = True
                    break
            if not matched:
                merged_items.append(new_item)

        existing_order.items_json = merged_items
        existing_order.total_amount = Decimal(str(existing_order.total_amount)) + total_amount
        if customer_note:
            if existing_order.customer_note:
                existing_order.customer_note = f"{existing_order.customer_note} | Extra: {customer_note}"
            else:
                existing_order.customer_note = customer_note

        # If it was marked served earlier, set back to preparing for the new items
        if existing_order.status == 'served':
            existing_order.status = 'preparing'

        existing_order.save(update_fields=['items_json', 'total_amount', 'customer_note', 'status'])
        order = existing_order
        is_add_on = True
    else:
        order = OrderLog.objects.create(
            restaurant=restaurant,
            session=session,
            table_number=table_number,
            items_json=items,
            total_amount=total_amount,
            customer_note=customer_note,
            status='sent',
            payment_method=payment_method,
            payment_status=payment_status,
        )
        is_add_on = False

    tracking_url = reverse('public:order_tracking', kwargs={'slug': restaurant.slug, 'order_id': order.id})

    # Real-time WebSocket push notifications:
    # 1. Alert Restaurant Cashier & Kitchen Dashboard
    # 2. Alert all connected diners at this table to redirect together to tracking page
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            # Broadcast to Kitchen & Dashboard
            async_to_sync(channel_layer.group_send)(
                f"restaurant_orders_{restaurant.slug}",
                {
                    'type': 'new_order_event',
                    'order': {
                        'id': order.id,
                        'table_number': order.table_number,
                        'total_amount': float(order.total_amount),
                        'items_summary': order.items_summary,
                        'customer_note': order.customer_note,
                        'payment_status': order.payment_status,
                        'payment_method': order.payment_method,
                        'status': order.status,
                        'diners': active_session.active_diners if active_session else [],
                        'created_at': order.created_at.strftime('%I:%M %p, %d %b'),
                    }
                }
            )

            # Broadcast to ALL phones at this table: redirect together!
            table_group = f"cart_{restaurant.slug}_{clean_table}"
            async_to_sync(channel_layer.group_send)(
                table_group,
                {
                    'type': 'order_redirect_broadcast',
                    'order_id': order.id,
                    'tracking_url': tracking_url,
                    'actor': data.get('diner_name', 'Someone at your table'),
                }
            )
    except Exception:
        pass

    return JsonResponse({
        'status': 'ok',
        'order_id': order.id,
        'payment_status': order.payment_status,
        'tracking_url': tracking_url,
    })


def order_tracking(request, slug, order_id):
    """
    Live order tracking page for customer.
    Shows real-time preparation progress (Received -> Cooking -> Served -> Completed),
    consolidated order summary across running table session rounds,
    and the Pay / Request Bill prompt when served.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)
    order = get_object_or_404(restaurant.orders, pk=order_id)

    # If already paid, redirect straight to receipt
    if order.payment_status == 'paid':
        return redirect('public:receipt', slug=restaurant.slug, order_id=order.id)

    # Consolidated session orders for this table (Rounds 1, 2, 3...)
    if order.session:
        session_orders = order.session.orders.filter(~models.Q(status='cancelled')).order_by('created_at')
    else:
        session_orders = [order]

    # Calculate combined total and merged items
    combined_total = sum(Decimal(str(o.total_amount)) for o in session_orders)
    combined_items = []
    for o in session_orders:
        for it in (o.items_json or []):
            combined_items.append({
                'name': it.get('name', 'Dish'),
                'quantity': it.get('quantity', 1),
                'price': it.get('price', 0),
                'item_total': it.get('item_total', float(it.get('price', 0)) * int(it.get('quantity', 1))),
                'is_veg': it.get('is_veg', True),
                'round': o.id,
            })

    # Build UPI intent URI with combined running total
    upi_url = ''
    if restaurant.upi_id:
        import urllib.parse
        payee = urllib.parse.quote(restaurant.upi_payee_name or restaurant.name)
        note = urllib.parse.quote(f"Table {order.table_number} {restaurant.name}")
        upi_url = f"upi://pay?pa={urllib.parse.quote(restaurant.upi_id)}&pn={payee}&am={combined_total:.2f}&cu=INR&tn={note}"

    return render(request, 'public/track_order.html', {
        'restaurant': restaurant,
        'order': order,
        'session_orders': session_orders,
        'combined_items': combined_items,
        'combined_total': combined_total,
        'upi_url': upi_url,
    })


@require_GET
def check_order_status(request, slug, order_id):
    """
    Live status polling endpoint for customer tracking page.
    Returns kitchen preparation status, payment status, payment_requested flag,
    and receipt URL once cashier marks the order as paid.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)
    order = get_object_or_404(restaurant.orders, pk=order_id)

    receipt_url = reverse('public:receipt', kwargs={'slug': slug, 'order_id': order.id})

    return JsonResponse({
        'order_id': order.id,
        'status': order.status,
        'status_display': order.get_status_display(),
        'payment_status': order.payment_status,
        'payment_status_display': order.get_payment_status_display(),
        'payment_requested': order.payment_requested,
        'is_paid': order.payment_status == 'paid',
        'paid_at': order.paid_at.isoformat() if order.paid_at else None,
        'receipt_url': receipt_url if order.payment_status == 'paid' else None,
    })


@require_POST
def submit_upi_payment(request, slug):
    """
    Called when customer taps 'Pay via UPI' or submits their UTR number.
    Marks payment_status as 'pending' so it flashes on the cashier dashboard.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON data.")

    order_id = data.get('order_id')
    order = get_object_or_404(restaurant.orders, pk=order_id)

    upi_utr = str(data.get('upi_utr', '')).strip()

    # Mark this order and any other orders in the active running table session as pending
    if order.session:
        orders_to_update = order.session.orders.filter(~models.Q(payment_status='paid'))
    else:
        orders_to_update = [order]

    for o in orders_to_update:
        o.payment_status = 'pending'
        if upi_utr:
            o.upi_utr = upi_utr
        o.save(update_fields=['payment_status', 'upi_utr'])

    # Broadcast payment update to restaurant dashboard
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"restaurant_orders_{restaurant.slug}",
                {
                    'type': 'payment_update_event',
                    'order_id': order.id,
                    'payment_status': order.payment_status,
                    'upi_utr': order.upi_utr,
                    'total_amount': float(order.total_amount),
                    'table_number': order.table_number,
                }
            )
    except Exception:
        pass

    return JsonResponse({
        'status': 'ok',
        'order_id': order.id,
        'payment_status': order.payment_status,
        'upi_utr': order.upi_utr,
    })


@require_GET
def check_payment_status(request, slug, order_id):
    """
    Polled by the customer's phone to check if cashier clicked 'Confirm Payment'.
    Returns current status and receipt URL once verified.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)
    order = get_object_or_404(restaurant.orders, pk=order_id)

    receipt_url = reverse('public:receipt', kwargs={'slug': slug, 'order_id': order.id})

    return JsonResponse({
        'order_id': order.id,
        'payment_status': order.payment_status,
        'is_paid': order.payment_status == 'paid',
        'paid_at': order.paid_at.isoformat() if order.paid_at else None,
        'receipt_url': receipt_url if order.payment_status == 'paid' else None,
    })


def order_receipt(request, slug, order_id):
    """
    Paperless digital invoice & receipt page for the customer.
    Displays items, totals, payment details, and Google Review button.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)
    order = get_object_or_404(restaurant.orders, pk=order_id)

    return render(request, 'public/receipt.html', {
        'restaurant': restaurant,
        'order': order,
    })
