from django.shortcuts import redirect


def index(request):
    """
    Root entrypoint:
    Redirects authenticated owners to restaurant dashboard,
    platform staff/superusers to platform admin,
    and unauthenticated visitors to login.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('platform:dashboard')
        from core.decorators import get_store_role
        role, _ = get_store_role(request.user)
        if role in ('cashier', 'waiter', 'kitchen'):
            return redirect('dashboard:orders')
        return redirect('dashboard:home')
    return redirect('login')
