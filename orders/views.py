from collections import defaultdict
from datetime import datetime, time, timedelta
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from core.decorators import owner_required
from .models import OrderLog


@owner_required
def dashboard_orders(request):
    """
    Owner view for order records, status transitions, and cashier UPI confirmations.
    Strictly scoped to the logged-in owner's restaurant with date-range filters and pagination.
    """
    restaurant = request.restaurant
    orders_qs = restaurant.orders.all()

    # Filters: from_date, to_date, status, range, and search query
    search_q = request.GET.get('q', '').strip()
    from_date_str = request.GET.get('from_date', '').strip()
    to_date_str = request.GET.get('to_date', '').strip()
    date_filter = request.GET.get('range', '').strip()
    status_filter = request.GET.get('status', '').strip()

    now = timezone.now()
    local_now = timezone.localtime(now)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Date filtering
    if from_date_str or to_date_str:
        if from_date_str:
            try:
                from_d = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                from_dt = timezone.make_aware(datetime.combine(from_d, time.min))
                orders_qs = orders_qs.filter(created_at__gte=from_dt)
            except ValueError:
                from_date_str = ''
        if to_date_str:
            try:
                to_d = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                to_dt = timezone.make_aware(datetime.combine(to_d, time.max))
                orders_qs = orders_qs.filter(created_at__lte=to_dt)
            except ValueError:
                to_date_str = ''
    elif date_filter:
        if date_filter == 'today':
            orders_qs = orders_qs.filter(created_at__gte=today_start)
        elif date_filter == 'yesterday':
            yesterday_start = today_start - timedelta(days=1)
            orders_qs = orders_qs.filter(created_at__gte=yesterday_start, created_at__lt=today_start)
        elif date_filter == '7days':
            seven_days_ago = now - timedelta(days=7)
            orders_qs = orders_qs.filter(created_at__gte=seven_days_ago)
        elif date_filter == '30days':
            thirty_days_ago = now - timedelta(days=30)
            orders_qs = orders_qs.filter(created_at__gte=thirty_days_ago)
        # 'all' does not filter by date

    # Status Filter
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    # Search Query: Order ID, Table number, customer note, UTR, or dish names
    if search_q:
        q_filter = (
            Q(table_number__icontains=search_q) |
            Q(customer_note__icontains=search_q) |
            Q(upi_utr__icontains=search_q) |
            Q(items_json__icontains=search_q)
        )
        clean_id = search_q.lstrip('#').strip()
        if clean_id.isdigit():
            q_filter |= Q(id=int(clean_id))
        orders_qs = orders_qs.filter(q_filter)

    # Order by newest first
    orders_qs = orders_qs.order_by('-created_at')

    # Popular dishes aggregation (needed for tests and analytics context)
    dish_stats = defaultdict(lambda: {'count': 0, 'revenue': 0.0, 'is_veg': True})
    table_stats = defaultdict(lambda: {'count': 0, 'revenue': 0.0})

    for order in orders_qs.filter(~Q(status='cancelled')):
        table_stats[order.table_number]['count'] += 1
        table_stats[order.table_number]['revenue'] += float(order.total_amount)

        for item in order.items_json:
            name = item.get('name', 'Unknown')
            qty = int(item.get('quantity', 1))
            price = float(item.get('price', 0))
            is_veg = bool(item.get('is_veg', True))

            dish_stats[name]['count'] += qty
            dish_stats[name]['revenue'] += (qty * price)
            dish_stats[name]['is_veg'] = is_veg

    popular_dishes = sorted(
        [{'name': k, **v} for k, v in dish_stats.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:6]

    orders_by_table = sorted(
        [{'table': k, **v} for k, v in table_stats.items()],
        key=lambda x: x['count'],
        reverse=True
    )
    most_active_table = orders_by_table[0]['table'] if orders_by_table else None

    # Key Metrics
    today_orders = restaurant.orders.filter(created_at__gte=today_start)
    today_count = today_orders.count()
    today_sales = today_orders.filter(~Q(status='cancelled')).aggregate(s=Sum('total_amount'))['s'] or 0

    total_orders_count = orders_qs.count()
    pending_payments_count = restaurant.orders.filter(payment_status='pending').count()

    # Pagination: 15 orders per page
    paginator = Paginator(orders_qs, 15)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Attach live seated diners & enriched item details (with photos) to each order
    import json
    from menu.models import MenuItem
    from orders.models import TableSession
    from public.consumers import get_table_diners

    menu_lookup = {}
    for m in MenuItem.objects.filter(restaurant=restaurant).only('id', 'name', 'photo', 'is_veg'):
        photo_url = m.photo.url if m.photo else ''
        menu_lookup[str(m.id)] = {'photo': photo_url, 'is_veg': m.is_veg}
        menu_lookup[m.name.lower()] = {'photo': photo_url, 'is_veg': m.is_veg}

    active_sessions = {
        str(s.table_number): s.active_diners or []
        for s in TableSession.objects.filter(restaurant=restaurant, is_active=True)
    }
    for o in page_obj:
        t_num = str(o.table_number).strip()
        live = get_table_diners(restaurant.slug, t_num)
        o.live_diners = live if live else active_sessions.get(t_num, [])

        enriched_items = []
        for it in (o.items_json or []):
            item_id = str(it.get('id', ''))
            item_name = str(it.get('name', 'Item'))
            qty = int(it.get('quantity', 1))
            price = float(it.get('price', 0))
            meta = menu_lookup.get(item_id) or menu_lookup.get(item_name.lower()) or {}
            enriched_items.append({
                'id': item_id,
                'name': item_name,
                'quantity': qty,
                'price': price,
                'item_total': float(it.get('item_total', price * qty)),
                'photo': it.get('photo') or meta.get('photo', ''),
                'is_veg': it.get('is_veg', meta.get('is_veg', True)),
                'added_by': it.get('added_by', ''),
            })
        o.enriched_items = enriched_items
        o.enriched_items_json = json.dumps(enriched_items)

    context = {
        'restaurant': restaurant,
        'orders': page_obj,
        'page_obj': page_obj,
        'total_orders_count': total_orders_count,
        'search_query': search_q,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'today_count': today_count,
        'today_sales': today_sales,
        'popular_dishes': popular_dishes,
        'orders_by_table': orders_by_table,
        'most_active_table': most_active_table,
        'pending_payments_count': pending_payments_count,
    }
    return render(request, 'dashboard/orders.html', context)


@owner_required
def order_update_status(request, pk):
    """Update order status (e.g. mark completed or cancelled)."""
    if request.method == 'POST':
        restaurant = request.restaurant
        order = get_object_or_404(restaurant.orders, pk=pk)
        new_status = request.POST.get('status', '').strip()

        if new_status in dict(OrderLog.STATUS_CHOICES):
            order.status = new_status
            order.save(update_fields=['status'])
            messages.success(request, f"Order from Table {order.table_number} marked as {order.get_status_display()}.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard:orders'))


@owner_required
def order_update_payment_status(request, pk):
    """
    Cashier confirmation for zero-fee direct UPI / cash payments.
    Marks payment as 'paid' or 'rejected'. Supports both AJAX and form POST.
    """
    if request.method == 'POST':
        restaurant = request.restaurant
        order = get_object_or_404(restaurant.orders, pk=pk)
        new_payment_status = request.POST.get('payment_status', '').strip()

        if new_payment_status in dict(OrderLog.PAYMENT_STATUS_CHOICES):
            order.payment_status = new_payment_status
            if new_payment_status == 'paid':
                order.paid_at = timezone.now()
            elif new_payment_status == 'unpaid':
                order.paid_at = None

            new_payment_method = request.POST.get('payment_method', '').strip()
            update_fields = ['payment_status', 'paid_at']
            if new_payment_method:
                order.payment_method = new_payment_method
                update_fields.append('payment_method')

            order.save(update_fields=update_fields)

            # If order belongs to an active table session, update all running orders in this session
            if order.session:
                session_orders = order.session.orders.exclude(pk=order.pk).filter(~Q(status='cancelled'))
                for so in session_orders:
                    so.payment_status = new_payment_status
                    so.paid_at = order.paid_at
                    if new_payment_method:
                        so.payment_method = new_payment_method
                    so.save(update_fields=update_fields)

            msg = f"Table {order.table_number} payment verified as {order.get_payment_status_display()}."
            messages.success(request, msg)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                from django.http import JsonResponse
                return JsonResponse({
                    'status': 'ok',
                    'order_id': order.id,
                    'payment_status': order.payment_status,
                    'paid_at': order.paid_at.isoformat() if order.paid_at else None,
                })

    return redirect(request.META.get('HTTP_REFERER', 'dashboard:orders'))


@owner_required
def order_request_payment(request, pk):
    """
    Triggered by admin/waiter to prompt the customer's live tracking screen
    for payment after food has been served.
    """
    if request.method == 'POST':
        restaurant = request.restaurant
        order = get_object_or_404(restaurant.orders, pk=pk)
        order.payment_requested = True
        order.save(update_fields=['payment_requested'])
        messages.success(request, f"Payment requested for Table {order.table_number}. The payment dialog is now shown on the customer's phone.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard:orders'))


@owner_required
def table_clear_session(request, table_number):
    """
    Clears an active table session once customers finish and leave.
    Closes the session so past diners cannot place ghost orders from outside.
    Broadcasts table_cleared_broadcast to disconnect/clear open browser tabs.
    """
    if request.method == 'POST':
        import re
        from orders.models import TableSession
        clean_table = re.sub(r'[^a-zA-Z0-9_\-]', '', str(table_number).strip())
        restaurant = request.restaurant

        active_sessions = TableSession.objects.filter(
            restaurant=restaurant,
            table_number=clean_table,
            is_active=True
        )
        # Clear in-memory presence tracking for this table
        from public.consumers import CONNECTED_TABLE_DINERS
        CONNECTED_TABLE_DINERS.pop((restaurant.slug, clean_table), None)

        for s in active_sessions:
            s.is_active = False
            s.active_diners = []
            s.save(update_fields=['is_active', 'active_diners', 'updated_at'])
            s.cart_items.all().delete()

        # Broadcast table cleared event over table WebSocket group
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"cart_{restaurant.slug}_{clean_table}",
                    {
                        'type': 'table_cleared_broadcast',
                        'table_number': clean_table,
                        'message': 'Table session ended by cashier.',
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    f"restaurant_orders_{restaurant.slug}",
                    {
                        'type': 'table_presence_event',
                        'table_number': clean_table,
                        'diners': [],
                        'count': 0,
                    }
                )
        except Exception:
            pass

        messages.success(request, f"Table {table_number} has been cleared and reset for the next guests.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard:orders'))
