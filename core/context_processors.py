import time
from django.conf import settings


def static_version(request):
    """
    Global context processor:
    - Provides cache-busting timestamp STATIC_VERSION
    - Exposes impersonation state across all templates
    - Exposes latest 5 notifications for restaurant dashboard topnav
    """
    version = int(time.time()) if settings.DEBUG else getattr(settings, 'APP_VERSION', '1.0.0')
    session = getattr(request, 'session', {})

    context = {
        'STATIC_VERSION': version,
        'is_impersonating': bool(session.get('impersonator_id')),
        'impersonated_restaurant_name': session.get('impersonated_restaurant_name'),
        'impersonated_restaurant_id': session.get('impersonated_restaurant_id'),
    }

    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        restaurant = getattr(request, 'restaurant', None)
        if not restaurant and hasattr(user, 'owner_profile'):
            restaurant = user.owner_profile.restaurant
        if restaurant:
            context['topnav_notifications'] = restaurant.orders.order_by('-created_at')[:5]

    return context
