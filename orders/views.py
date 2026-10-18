from collections import defaultdict
from datetime import timedelta
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from core.decorators import owner_required
from .models import OrderLog


@owner_required
def dashboard_orders(request):
    """
    Phase 4: Owner view for order history, popular dishes, and orders per table.
    Strictly scoped to the logged-in owner's restaurant.
    """
    restaurant = request.restaurant
    orders_qs = restaurant.orders.all()

    # Date Range Filter
    date_filter = request.GET.get('range', 'today').strip()
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

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
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    # 1. Today's Key Metrics
    today_orders = restaurant.orders.filter(created_at__gte=today_start)
    today_count = today_orders.count()
    today_sales = today_orders.filter(~Q(status='cancelled')).aggregate(s=Sum('total_amount'))['s'] or 0

    # 2. Filtered Range Metrics
    filtered_count = orders_qs.count()
    filtered_sales = orders_qs.filter(~Q(status='cancelled')).aggregate(s=Sum('total_amount'))['s'] or 0

    # 3. Analytics: Popular Dishes (aggregated from items_json)
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

    # Sort popular dishes by quantity sold descending
    popular_dishes = sorted(
        [{'name': k, **v} for k, v in dish_stats.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:6]

    # Sort tables by order volume descending
    orders_by_table = sorted(
        [{'table': k, **v} for k, v in table_stats.items()],
        key=lambda x: x['count'],
        reverse=True
    )

    most_active_table = orders_by_table[0]['table'] if orders_by_table else None

    context = {
        'restaurant': restaurant,
        'orders': orders_qs[:100],  # Latest 100 orders in range
        'today_count': today_count,
        'today_sales': today_sales,
        'filtered_count': filtered_count,
        'filtered_sales': filtered_sales,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'popular_dishes': popular_dishes,
        'orders_by_table': orders_by_table,
        'most_active_table': most_active_table,
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
