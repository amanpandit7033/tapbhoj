from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import OwnerProfile
from restaurants.models import Restaurant
from .models import Plan, Subscription


class PlatformAdminAndBillingTests(TestCase):
    def setUp(self):
        # Staff user
        self.staff_user = User.objects.create_user(
            username='staff', email='staff@tapbhoj.in', password='Password@123', is_staff=True
        )

        # Normal owner user & restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Bistro',
            slug='test-bistro',
            whatsapp_number='919876543210',
            status='active',
            number_of_tables=8
        )
        self.owner_user = User.objects.create_user(
            username='bistro_owner', email='owner@bistro.com', password='Password@123', is_staff=False
        )
        self.profile = OwnerProfile.objects.create(
            user=self.owner_user, restaurant=self.restaurant
        )

        # Plan
        self.plan = Plan.objects.create(
            name='Starter Plan',
            slug='starter',
            price=Decimal('499.00'),
            duration_days=30,
            is_active=True
        )

        self.subscription = Subscription.objects.create(
            restaurant=self.restaurant,
            plan=self.plan,
            status='trialing'
        )
        self.subscription.activate_trial(trial_days=14)

    def test_non_staff_denied_platform_admin(self):
        """Non-staff users must not be allowed into /platform/."""
        # Unauthenticated
        response = self.client.get(reverse('platform:dashboard'))
        self.assertEqual(response.status_code, 302)

        # Authenticated as regular owner
        self.client.login(username='bistro_owner', password='Password@123')
        response = self.client.get(reverse('platform:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_view_platform_dashboard(self):
        """Staff user can access /platform/ and view metrics."""
        self.client.login(username='staff', password='Password@123')
        response = self.client.get(reverse('platform:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'platform/dashboard.html')
        self.assertContains(response, 'Test Bistro')
        self.assertContains(response, 'Restaurant Management')

    def test_one_step_onboarding(self):
        """Requirement A1: Single form creates restaurant, owner account, profile, and trial."""
        self.client.login(username='staff', password='Password@123')
        url = reverse('platform:restaurant_create')

        post_data = {
            'restaurant_name': 'New Dhaba',
            'slug': 'new-dhaba',
            'whatsapp_number': '919876543299',
            'number_of_tables': 15,
            'address': 'Highway 1',
            'owner_username': 'dhaba_owner',
            'owner_email': 'owner@newdhaba.com',
            'owner_password': 'SecurePassword@123',
            'trial_days': 21,
            'initial_plan': self.plan.pk,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        # Verify restaurant created
        new_restaurant = Restaurant.objects.get(slug='new-dhaba')
        self.assertEqual(new_restaurant.name, 'New Dhaba')
        self.assertEqual(new_restaurant.status, 'active')

        # Verify user and profile created
        new_user = User.objects.get(username='dhaba_owner')
        self.assertEqual(new_user.email, 'owner@newdhaba.com')
        self.assertTrue(new_user.check_password('SecurePassword@123'))
        self.assertEqual(new_user.owner_profile.restaurant, new_restaurant)

        # Verify subscription created with 21-day trial
        sub = new_restaurant.subscription
        self.assertEqual(sub.status, 'trialing')
        self.assertTrue(sub.is_valid)

        # Verify welcome email sent
        self.assertTrue(len(mail.outbox) >= 1)
        self.assertIn('Welcome to TapBhoj', mail.outbox[-1].subject)

    def test_platform_toggle_restaurant(self):
        """Requirement A2: Staff can pause or activate restaurant with 1 click."""
        self.client.login(username='staff', password='Password@123')
        url = reverse('platform:restaurant_toggle', kwargs={'pk': self.restaurant.pk})

        # Pause
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.status, 'paused')

        # Activate
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.status, 'active')

    def test_platform_assist_impersonation(self):
        """Requirement A6: Staff can assist owner and gets switched to owner dashboard."""
        self.client.login(username='staff', password='Password@123')
        url = reverse('platform:restaurant_assist', kwargs={'pk': self.restaurant.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:home'))

        # Verify current user in session is now bistro_owner
        dashboard_res = self.client.get(reverse('dashboard:home'))
        self.assertEqual(dashboard_res.status_code, 200)
        self.assertContains(dashboard_res, 'Test Bistro')

    def test_owner_subscription_renewal(self):
        """Requirement A5: Owner can renew subscription and extend validity."""
        self.client.login(username='bistro_owner', password='Password@123')
        url = reverse('dashboard:subscription_renew')

        post_data = {
            'plan_id': self.plan.pk,
            'razorpay_payment_id': 'pay_test123456',
            'razorpay_order_id': 'order_test123456',
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'active')
        self.assertEqual(self.subscription.razorpay_payment_id, 'pay_test123456')
        self.assertTrue(self.subscription.is_valid)

    def test_check_subscription_expiries_auto_pauses(self):
        """Management command auto-pauses restaurants whose subscription lapsed."""
        # Force expiry in the past
        past_date = timezone.now() - timedelta(days=2)
        self.subscription.status = 'trialing'
        self.subscription.trial_end = past_date
        self.subscription.save()

        self.restaurant.status = 'active'
        self.restaurant.save()

        # Run command
        call_command('check_subscription_expiries')

        self.subscription.refresh_from_db()
        self.restaurant.refresh_from_db()

        self.assertEqual(self.subscription.status, 'expired')
        self.assertEqual(self.restaurant.status, 'paused')
