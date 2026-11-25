import json
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
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

    # Fetch visible categories with pre-fetched menu items ordered by position (Requirement C3, Performance)
    categories = restaurant.categories.filter(is_visible=True).prefetch_related('items')

    context = {
        'restaurant': restaurant,
        'categories': categories,
        'table_number': table_number,
    }
    return render(request, 'public/menu.html', context)


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

    payment_method = str(data.get('payment_method', 'upi_direct')).strip()
    payment_status = str(data.get('payment_status', 'unpaid')).strip()
    if payment_status not in dict(OrderLog.PAYMENT_STATUS_CHOICES):
        payment_status = 'unpaid'

    order = OrderLog.objects.create(
        restaurant=restaurant,
        table_number=table_number,
        items_json=items,
        total_amount=total_amount,
        customer_note=customer_note,
        status='sent',
        payment_method=payment_method,
        payment_status=payment_status,
    )

    # Real-time WebSocket push notification to Dashboard
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
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
                        'created_at': order.created_at.strftime('%I:%M %p, %d %b'),
                    }
                }
            )
    except Exception:
        pass

    return JsonResponse({
        'status': 'ok',
        'order_id': order.id,
        'payment_status': order.payment_status,
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
    order.payment_status = 'pending'
    if upi_utr:
        order.upi_utr = upi_utr
    order.save(update_fields=['payment_status', 'upi_utr'])

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
