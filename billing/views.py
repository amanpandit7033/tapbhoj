from collections import Counter, defaultdict
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from accounts.models import OwnerProfile
from core.decorators import owner_required
from menu.models import MenuItem
from orders.models import OrderLog
from restaurants.models import Restaurant
from .forms import (
    OwnerAccountEditForm,
    RestaurantEditForm,
    RestaurantOnboardForm,
    SubscriptionEditForm,
)
from .models import Plan, Subscription


# ==============================================================================
# Platform Admin Views (Restricted to TapBhoj Staff)
# ==============================================================================

@staff_member_required(login_url='login')
def platform_dashboard(request):
    """Platform admin overview of all restaurants, statuses, and subscriptions."""
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

    restaurants = Restaurant.objects.all().select_related('subscription').prefetch_related('owners__user')

    if status_filter:
        restaurants = restaurants.filter(status=status_filter)

    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(whatsapp_number__icontains=search_query)
        )

    # Key Platform Stats
    total_count = Restaurant.objects.count()
    active_count = Restaurant.objects.filter(status='active').count()
    trial_count = Subscription.objects.filter(status='trialing').count()
    paused_count = Restaurant.objects.filter(status='paused').count()

    # Expiring soon (within next 7 days)
    seven_days_later = timezone.now() + timedelta(days=7)
    expiring_soon_count = Subscription.objects.filter(
        Q(status='trialing', trial_end__lte=seven_days_later, trial_end__gte=timezone.now()) |
        Q(status='active', current_period_end__lte=seven_days_later, current_period_end__gte=timezone.now())
    ).count()

    context = {
        'restaurants': restaurants,
        'total_count': total_count,
        'active_count': active_count,
        'trial_count': trial_count,
        'paused_count': paused_count,
        'expiring_soon_count': expiring_soon_count,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'platform/dashboard.html', context)


@staff_member_required(login_url='login')
def platform_restaurant_create(request):
    """
    Requirement A1: Create restaurant + owner account + trial subscription in 1 single step.
    Sends welcome credentials email to owner.
    """
    if request.method == 'POST':
        form = RestaurantOnboardForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # 1. Create Restaurant
                restaurant = Restaurant.objects.create(
                    name=form.cleaned_data['restaurant_name'],
                    slug=form.cleaned_data['slug'],
                    whatsapp_number=form.cleaned_data['whatsapp_number'],
                    number_of_tables=form.cleaned_data['number_of_tables'],
                    address=form.cleaned_data['address'],
                    status='active'
                )

                # 2. Create Owner User
                user = User.objects.create_user(
                    username=form.cleaned_data['owner_username'],
                    email=form.cleaned_data['owner_email'],
                    password=form.cleaned_data['owner_password'],
                    is_staff=False
                )

                # 3. Create Owner Profile
                OwnerProfile.objects.create(
                    user=user,
                    restaurant=restaurant
                )

                # 4. Create Subscription with Trial
                subscription = Subscription.objects.create(
                    restaurant=restaurant,
                    plan=form.cleaned_data.get('initial_plan'),
                    status='trialing'
                )
                trial_days = form.cleaned_data.get('trial_days', 14)
                subscription.activate_trial(trial_days=trial_days)

                # 5. Send Welcome Email
                login_url = request.build_absolute_uri(reverse('login'))
                subject = f"Welcome to TapBhoj - Your Digital Menu is Ready ({restaurant.name})"
                message = (
                    f"Hello,\n\n"
                    f"Your TapBhoj restaurant account for '{restaurant.name}' has been created!\n\n"
                    f"Login Details:\n"
                    f"Dashboard URL: {login_url}\n"
                    f"Username: {user.username}\n"
                    f"Password: {form.cleaned_data['owner_password']}\n\n"
                    f"Public Menu URL: {request.build_absolute_uri(reverse('public:menu', kwargs={'slug': restaurant.slug}))}\n\n"
                    f"You have a {trial_days}-day free trial active until {subscription.trial_end.strftime('%d %b %Y')}.\n\n"
                    f"Welcome aboard!\nTapBhoj Team"
                )
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True
                    )
                except Exception:
                    pass

            messages.success(request, f'Restaurant "{restaurant.name}" and owner account "{user.username}" created successfully!')
            return redirect('platform:restaurant_detail', pk=restaurant.pk)
    else:
        form = RestaurantOnboardForm()

    return render(request, 'platform/restaurant_create.html', {'form': form})


@staff_member_required(login_url='login')
def platform_restaurant_detail(request, pk):
    """View and manage restaurant details, owner account, menu items, orders, and subscription."""
    restaurant = get_object_or_404(
        Restaurant.objects.select_related('subscription').prefetch_related('owners__user'),
        pk=pk
    )
    subscription, _ = Subscription.objects.get_or_create(restaurant=restaurant)
    owner_profile = restaurant.owners.first()
    owner_user = owner_profile.user if owner_profile else None

    tab = request.GET.get('tab', 'overview')

    restaurant_form = RestaurantEditForm(instance=restaurant)
    owner_form = OwnerAccountEditForm(initial={'email': owner_user.email}) if owner_user else None
    sub_form = SubscriptionEditForm(instance=subscription)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_restaurant':
            restaurant_form = RestaurantEditForm(request.POST, instance=restaurant)
            if restaurant_form.is_valid():
                restaurant_form.save()
                messages.success(request, f'Restaurant profile for "{restaurant.name}" updated successfully.')
                return redirect(f"{reverse('platform:restaurant_detail', kwargs={'pk': restaurant.pk})}?tab=settings")

        elif action == 'update_owner' and owner_user:
            owner_form = OwnerAccountEditForm(request.POST)
            if owner_form.is_valid():
                owner_user.email = owner_form.cleaned_data['email']
                new_pw = owner_form.cleaned_data.get('new_password')
                if new_pw:
                    owner_user.set_password(new_pw)
                    messages.success(request, f'Password for owner "{owner_user.username}" reset successfully!')
                else:
                    messages.success(request, f'Owner account "{owner_user.username}" updated.')
                owner_user.save()
                return redirect(f"{reverse('platform:restaurant_detail', kwargs={'pk': restaurant.pk})}?tab=settings")

        elif action == 'update_subscription':
            sub_form = SubscriptionEditForm(request.POST, instance=subscription)
            if sub_form.is_valid():
                sub_form.save()
                messages.success(request, 'Subscription settings updated successfully.')
                return redirect(f"{reverse('platform:restaurant_detail', kwargs={'pk': restaurant.pk})}?tab=subscription")

    # Categories & items for menu tab
    categories = restaurant.categories.prefetch_related('items').all()
    total_items_count = sum(c.items.count() for c in categories)

    # Orders for orders tab
    orders = restaurant.orders.all()[:50]
    orders_count = restaurant.orders.count()
    orders_total = restaurant.orders.aggregate(s=Sum('total_amount'))['s'] or 0

    return render(request, 'platform/restaurant_detail.html', {
        'restaurant': restaurant,
        'subscription': subscription,
        'owner': owner_user,
        'restaurant_form': restaurant_form,
        'owner_form': owner_form,
        'form': sub_form,
        'sub_form': sub_form,
        'categories': categories,
        'total_items_count': total_items_count,
        'orders': orders,
        'orders_count': orders_count,
        'orders_total': orders_total,
        'active_tab': tab,
    })


@staff_member_required(login_url='login')
def platform_toggle_restaurant(request, pk):
    """Requirement A2: 1-click activate or pause restaurant from platform admin."""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if restaurant.status == 'active':
        restaurant.status = 'paused'
        messages.info(request, f'"{restaurant.name}" is now paused.')
    else:
        restaurant.status = 'active'
        messages.success(request, f'"{restaurant.name}" is now active.')
    restaurant.save()
    return redirect('platform:dashboard')


@staff_member_required(login_url='login')
def platform_restaurant_delete(request, pk):
    """Safely delete restaurant and associated non-staff owner."""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        name = restaurant.name
        owner_users = [op.user for op in restaurant.owners.all() if not op.user.is_staff]
        with transaction.atomic():
            restaurant.delete()
            for u in owner_users:
                if not OwnerProfile.objects.filter(user=u).exists():
                    u.delete()
        messages.success(request, f'Restaurant "{name}" and its data have been permanently deleted.')
        return redirect('platform:dashboard')

    return render(request, 'platform/restaurant_confirm_delete.html', {'restaurant': restaurant})


@staff_member_required(login_url='login')
def platform_clear_test_orders(request, pk):
    """Purge test orders for a restaurant."""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        count = restaurant.orders.count()
        restaurant.orders.all().delete()
        messages.success(request, f'Successfully purged {count} order record(s) for "{restaurant.name}".')
    return redirect(f"{reverse('platform:restaurant_detail', kwargs={'pk': restaurant.pk})}?tab=orders")


@staff_member_required(login_url='login')
def platform_item_toggle(request, pk):
    """1-click toggle menu item availability directly from platform admin."""
    item = get_object_or_404(MenuItem, pk=pk)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available'])
    state = "available" if item.is_available else "sold out"
    messages.success(request, f'"{item.name}" marked as {state}.')
    return redirect(f"{reverse('platform:restaurant_detail', kwargs={'pk': item.restaurant.pk})}?tab=menu")


@staff_member_required(login_url='login')
def platform_impersonate(request, pk):
    """
    Requirement A6: Impersonate or assist an owner to enter their menu.
    Logs staff member in as the restaurant's owner user.
    """
    restaurant = get_object_or_404(Restaurant, pk=pk)
    owner_profile = restaurant.owners.first()
    if not owner_profile or not owner_profile.user:
        messages.error(request, f'No owner user account found for "{restaurant.name}".')
        return redirect('platform:restaurant_detail', pk=pk)

    owner_user = owner_profile.user
    auth_login(request, owner_user)
    messages.info(request, f'Now assisting as "{owner_user.username}" for restaurant "{restaurant.name}".')
    return redirect('dashboard:home')


@staff_member_required(login_url='login')
def platform_live_orders(request):
    """Cross-store live orders feed across all restaurants."""
    restaurant_id = request.GET.get('restaurant', '').strip()
    status_filter = request.GET.get('status', '').strip()
    table_query = request.GET.get('table', '').strip()

    orders_qs = OrderLog.objects.select_related('restaurant').all()

    if restaurant_id:
        orders_qs = orders_qs.filter(restaurant_id=restaurant_id)
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)
    if table_query:
        orders_qs = orders_qs.filter(table_number__icontains=table_query)

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders_count = OrderLog.objects.filter(created_at__gte=today_start).count()
    today_gmv = OrderLog.objects.filter(created_at__gte=today_start).aggregate(s=Sum('total_amount'))['s'] or 0
    total_gmv = OrderLog.objects.aggregate(s=Sum('total_amount'))['s'] or 0
    total_orders_count = OrderLog.objects.count()

    restaurants = Restaurant.objects.all().order_by('name')
    orders = orders_qs[:100]

    return render(request, 'platform/live_orders.html', {
        'orders': orders,
        'restaurants': restaurants,
        'selected_restaurant': restaurant_id,
        'selected_status': status_filter,
        'table_query': table_query,
        'today_orders_count': today_orders_count,
        'today_gmv': today_gmv,
        'total_gmv': total_gmv,
        'total_orders_count': total_orders_count,
    })


@staff_member_required(login_url='login')
def platform_analytics(request):
    """Platform-wide analytics dashboard."""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    total_orders = OrderLog.objects.count()
    total_gmv = OrderLog.objects.aggregate(s=Sum('total_amount'))['s'] or 0

    today_orders = OrderLog.objects.filter(created_at__gte=today_start).count()
    today_gmv = OrderLog.objects.filter(created_at__gte=today_start).aggregate(s=Sum('total_amount'))['s'] or 0

    week_orders = OrderLog.objects.filter(created_at__gte=seven_days_ago).count()
    week_gmv = OrderLog.objects.filter(created_at__gte=seven_days_ago).aggregate(s=Sum('total_amount'))['s'] or 0

    aov = (total_gmv / total_orders) if total_orders > 0 else 0

    restaurant_stats = Restaurant.objects.annotate(
        order_count=Count('orders'),
        total_revenue=Sum('orders__total_amount')
    ).order_by('-total_revenue')

    dish_counter = Counter()
    dish_revenue = defaultdict(float)
    dish_veg = {}

    for o in OrderLog.objects.all():
        for item in (o.items_json or []):
            name = item.get('name')
            if name:
                qty = item.get('quantity', 1)
                price = float(item.get('price', 0))
                dish_counter[name] += qty
                dish_revenue[name] += qty * price
                dish_veg[name] = item.get('is_veg', True)

    top_dishes = []
    for name, qty in dish_counter.most_common(10):
        top_dishes.append({
            'name': name,
            'quantity': qty,
            'revenue': dish_revenue[name],
            'is_veg': dish_veg.get(name, True)
        })

    sub_stats = {
        'active': Subscription.objects.filter(status='active').count(),
        'trialing': Subscription.objects.filter(status='trialing').count(),
        'past_due': Subscription.objects.filter(status='past_due').count(),
        'cancelled': Subscription.objects.filter(status='cancelled').count(),
    }

    return render(request, 'platform/analytics.html', {
        'total_orders': total_orders,
        'total_gmv': total_gmv,
        'today_orders': today_orders,
        'today_gmv': today_gmv,
        'week_orders': week_orders,
        'week_gmv': week_gmv,
        'aov': aov,
        'restaurant_stats': restaurant_stats,
        'top_dishes': top_dishes,
        'sub_stats': sub_stats,
    })


@staff_member_required(login_url='login')
def platform_billing_overview(request):
    """Platform-wide billing and plans overview."""
    plans = Plan.objects.all()
    subscriptions = Subscription.objects.select_related('restaurant', 'plan').order_by('-created_at')

    return render(request, 'platform/billing_overview.html', {
        'plans': plans,
        'subscriptions': subscriptions,
    })



# ==============================================================================
# Owner Subscription & Renewal Views
# ==============================================================================

@owner_required
def owner_subscription(request):
    """Owner subscription status and renewal screen in owner dashboard."""
    restaurant = request.restaurant
    subscription, _ = Subscription.objects.get_or_create(restaurant=restaurant)
    plans = Plan.objects.filter(is_active=True)

    return render(request, 'dashboard/subscription.html', {
        'restaurant': restaurant,
        'subscription': subscription,
        'plans': plans,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    })


@owner_required
def owner_renew(request):
    """Simulate or execute plan renewal with Razorpay reference."""
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(Plan, pk=plan_id, is_active=True)
        subscription, _ = Subscription.objects.get_or_create(restaurant=request.restaurant)

        payment_id = request.POST.get('razorpay_payment_id', f'pay_sim_{timezone.now().timestamp():.0f}')
        order_id = request.POST.get('razorpay_order_id', f'order_sim_{timezone.now().timestamp():.0f}')

        subscription.renew(plan=plan, payment_id=payment_id, order_id=order_id)
        messages.success(request, f'Subscription renewed successfully for {plan.name}! Your menu is active.')

    return redirect('dashboard:subscription')
