import json
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
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

    order = OrderLog.objects.create(
        restaurant=restaurant,
        table_number=table_number,
        items_json=items,
        total_amount=total_amount,
        customer_note=customer_note,
        status='sent',
    )

    return JsonResponse({
        'status': 'ok',
        'order_id': order.id,
    })
