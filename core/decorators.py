from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def owner_required(view_func):
    """
    Decorator that ensures:
    1. The user is authenticated.
    2. The user has an active OwnerProfile linking them to a single Restaurant.
    3. The resolved restaurant is attached to `request.restaurant` so that all queries
       in the view are strictly tenant-scoped to that restaurant.
    """
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'owner_profile'):
            raise PermissionDenied("You do not have a restaurant owner account associated with this login.")
        request.restaurant = request.user.owner_profile.restaurant
        return view_func(request, *args, **kwargs)
    return _wrapped_view
