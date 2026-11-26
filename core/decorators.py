from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def get_store_role(user):
    """Return `(role, restaurant)` for an authenticated store owner or active staff member."""
    if not user or not user.is_authenticated:
        return None, None
    if hasattr(user, 'owner_profile'):
        return 'owner', user.owner_profile.restaurant
    if hasattr(user, 'staff_profile') and user.staff_profile.is_active:
        return user.staff_profile.role, user.staff_profile.restaurant
    return None, None


def role_required(*allowed_roles):
    """
    Decorator ensuring the user is an authenticated store owner or active staff member
    with one of `allowed_roles` (or any active store role if `allowed_roles` is empty).
    Attaches `request.restaurant`, `request.staff_role`, and `request.is_store_owner`.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            role, restaurant = get_store_role(request.user)
            if not role:
                raise PermissionDenied("You do not have a restaurant account associated with this login.")
            if allowed_roles and role not in allowed_roles:
                raise PermissionDenied("You do not have permission to access this section.")
            request.restaurant = restaurant
            request.staff_role = role
            request.is_store_owner = (role == 'owner')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


owner_required = role_required()
strict_owner_required = role_required('owner')
