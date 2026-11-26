from django.core.exceptions import ValidationError
from django.test import TestCase
from restaurants.models import Restaurant, validate_whatsapp_number


class RestaurantModelTests(TestCase):
    def test_valid_whatsapp_numbers(self):
        # Valid numbers: 10 to 15 digits
        validate_whatsapp_number('919876543210')
        validate_whatsapp_number('+919876543210')

    def test_invalid_whatsapp_numbers(self):
        # Invalid numbers with letters or too short
        with self.assertRaises(ValidationError):
            validate_whatsapp_number('9876')
        with self.assertRaises(ValidationError):
            validate_whatsapp_number('invalid-phone')

    def test_is_live_property(self):
        r1 = Restaurant.objects.create(
            name='R1', slug='r1', whatsapp_number='919876543210', status='active'
        )
        self.assertTrue(r1.is_live)

        r2 = Restaurant.objects.create(
            name='R2', slug='r2', whatsapp_number='919876543211', status='paused'
        )
        self.assertFalse(r2.is_live)


class StaffManagementTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from accounts.models import OwnerProfile, StaffMember

        User = get_user_model()
        self.r1 = Restaurant.objects.create(
            name='R1', slug='r1-staff', whatsapp_number='919876543210', status='active'
        )
        self.r2 = Restaurant.objects.create(
            name='R2', slug='r2-staff', whatsapp_number='919876543211', status='active'
        )
        self.owner1 = User.objects.create_user(username='owner1', password='pw1')
        OwnerProfile.objects.create(user=self.owner1, restaurant=self.r1)
        self.owner2 = User.objects.create_user(username='owner2', password='pw2')
        OwnerProfile.objects.create(user=self.owner2, restaurant=self.r2)
        self.StaffMember = StaffMember

    def test_owner_crud_staff(self):
        self.client.force_login(self.owner1)

        # GET staff page
        resp = self.client.get('/dashboard/staff/')
        self.assertEqual(resp.status_code, 200)

        # POST record-only staff
        resp = self.client.post('/dashboard/staff/', {
            'name': 'Raju Waiter',
            'role': 'waiter',
            'phone': '9876543210',
        })
        self.assertEqual(resp.status_code, 302)
        s1 = self.StaffMember.objects.get(restaurant=self.r1, name='Raju Waiter')
        self.assertIsNone(s1.user)
        self.assertTrue(s1.is_active)

        # POST login-enabled staff
        resp = self.client.post('/dashboard/staff/', {
            'name': 'Priya Manager',
            'role': 'manager',
            'phone': '9876543211',
            'username': 'priya_mgr',
            'password': 'secretpassword123',
        })
        self.assertEqual(resp.status_code, 302)
        s2 = self.StaffMember.objects.get(restaurant=self.r1, name='Priya Manager')
        self.assertIsNotNone(s2.user)
        self.assertFalse(s2.user.is_staff)
        self.assertTrue(s2.user.is_active)

        # Toggle active status
        resp = self.client.post(f'/dashboard/staff/{s2.pk}/toggle/')
        self.assertEqual(resp.status_code, 302)
        s2.refresh_from_db()
        s2.user.refresh_from_db()
        self.assertFalse(s2.is_active)
        self.assertFalse(s2.user.is_active)

        # Delete staff
        resp = self.client.post(f'/dashboard/staff/{s1.pk}/delete/')
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(self.StaffMember.objects.filter(pk=s1.pk).exists())

    def test_staff_access_and_tenant_isolation(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        staff_user = User.objects.create_user(username='chef1', password='pw')
        staff = self.StaffMember.objects.create(
            restaurant=self.r1, user=staff_user, name='Chef One', role='kitchen', is_active=True
        )

        # Active staff can access store operations (/dashboard/orders/)
        self.client.force_login(staff_user)
        resp = self.client.get('/dashboard/orders/')
        self.assertEqual(resp.status_code, 200)

        # Active staff is denied on strict owner-only /dashboard/staff/
        resp = self.client.get('/dashboard/staff/')
        self.assertEqual(resp.status_code, 403)

        # Inactive staff is denied on /dashboard/orders/
        staff.is_active = False
        staff.save()
        resp = self.client.get('/dashboard/orders/')
        self.assertEqual(resp.status_code, 403)

        # Tenant isolation: owner2 cannot toggle or delete r1's staff
        self.client.force_login(self.owner2)
        self.assertEqual(self.client.post(f'/dashboard/staff/{staff.pk}/toggle/').status_code, 404)
        self.assertEqual(self.client.post(f'/dashboard/staff/{staff.pk}/delete/').status_code, 404)


class RoleAccessMatrixTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from accounts.models import OwnerProfile, StaffMember
        from menu.models import Category, MenuItem
        from orders.models import OrderLog

        User = get_user_model()
        self.r = Restaurant.objects.create(
            name='Role Resto', slug='role-resto', whatsapp_number='919876543210', status='active'
        )
        self.owner = User.objects.create_user(username='r_owner', password='pw')
        OwnerProfile.objects.create(user=self.owner, restaurant=self.r)

        self.roles = {}
        for role in ('manager', 'cashier', 'waiter', 'kitchen'):
            u = User.objects.create_user(username=f'r_{role}', password='pw')
            StaffMember.objects.create(
                restaurant=self.r, user=u, name=role.title(), role=role, is_active=True
            )
            self.roles[role] = u

        cat = Category.objects.create(restaurant=self.r, name='Starters', position=1)
        self.item = MenuItem.objects.create(
            restaurant=self.r, category=cat, name='Paneer', price=100
        )
        self.order = OrderLog.objects.create(
            restaurant=self.r, table_number='1', total_amount=100, items_json=[]
        )

    def test_manager_access(self):
        self.client.force_login(self.roles['manager'])
        self.assertEqual(self.client.get('/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/orders/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/menu/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/menu/category/add/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/tables/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/staff/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/subscription/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/profile/').status_code, 403)

    def test_cashier_access(self):
        self.client.force_login(self.roles['cashier'])
        self.assertRedirects(self.client.get('/dashboard/'), '/dashboard/orders/')
        self.assertEqual(self.client.get('/dashboard/orders/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/menu/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/tables/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/staff/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/subscription/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/profile/').status_code, 403)
        self.assertEqual(
            self.client.post(f'/dashboard/orders/{self.order.pk}/status/', {'status': 'preparing'}).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(f'/dashboard/orders/{self.order.pk}/payment-status/', {'payment_status': 'paid'}).status_code,
            302,
        )

    def test_waiter_access(self):
        self.client.force_login(self.roles['waiter'])
        self.assertRedirects(self.client.get('/dashboard/'), '/dashboard/orders/')
        self.assertEqual(self.client.get('/dashboard/orders/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/tables/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/menu/').status_code, 200)
        self.assertEqual(self.client.post(f'/dashboard/menu/item/{self.item.pk}/toggle/').status_code, 302)
        self.assertEqual(self.client.get('/dashboard/menu/category/add/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/staff/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/subscription/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/profile/').status_code, 403)
        self.assertEqual(
            self.client.post(f'/dashboard/orders/{self.order.pk}/payment-status/', {'payment_status': 'paid'}).status_code,
            403,
        )

    def test_kitchen_access(self):
        self.client.force_login(self.roles['kitchen'])
        self.assertRedirects(self.client.get('/dashboard/'), '/dashboard/orders/')
        self.assertEqual(self.client.get('/dashboard/orders/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/menu/').status_code, 200)
        self.assertEqual(self.client.post(f'/dashboard/menu/item/{self.item.pk}/toggle/').status_code, 302)
        self.assertEqual(
            self.client.post(f'/dashboard/orders/{self.order.pk}/status/', {'status': 'preparing'}).status_code,
            302,
        )
        self.assertEqual(self.client.get('/dashboard/tables/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/menu/category/add/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/staff/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/subscription/').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/profile/').status_code, 403)
        self.assertEqual(
            self.client.post(f'/dashboard/orders/{self.order.pk}/payment-status/', {'payment_status': 'paid'}).status_code,
            403,
        )



