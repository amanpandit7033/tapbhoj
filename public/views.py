from django.shortcuts import get_object_or_404, render
from restaurants.models import Restaurant
from menu.models import Category


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
