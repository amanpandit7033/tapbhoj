from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from accounts.models import OwnerProfile
from core.decorators import owner_required
from restaurants.models import Restaurant
from .forms import RestaurantOnboardForm, SubscriptionEditForm
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
    """View and edit restaurant subscription details, trial periods, and status."""
    restaurant = get_object_or_404(
        Restaurant.objects.select_related('subscription').prefetch_related('owners__user'),
        pk=pk
    )
    subscription, _ = Subscription.objects.get_or_create(restaurant=restaurant)
    owner_profile = restaurant.owners.first()

    if request.method == 'POST':
        form = SubscriptionEditForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subscription updated successfully.')
            return redirect('platform:restaurant_detail', pk=restaurant.pk)
    else:
        form = SubscriptionEditForm(instance=subscription)

    return render(request, 'platform/restaurant_detail.html', {
        'restaurant': restaurant,
        'subscription': subscription,
        'owner': owner_profile.user if owner_profile else None,
        'form': form,
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
    # Log in as the owner user directly
    auth_login(request, owner_user)
    messages.info(request, f'Now assisting as "{owner_user.username}" for restaurant "{restaurant.name}".')
    return redirect('dashboard:home')


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
