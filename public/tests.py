from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from restaurants.models import Restaurant
from menu.models import Category, MenuItem


class PublicMenuTests(TestCase):
    def setUp(self):
        # Create an active restaurant
        self.active_restaurant = Restaurant.objects.create(
            name='Test Dhaba',
            slug='test-dhaba',
            whatsapp_number='919876543210',
            status='active',
            description='Homely punjabi meals',
            google_review_url='https://g.page/r/test-dhaba/review'
        )

        # Create a paused restaurant
        self.paused_restaurant = Restaurant.objects.create(
            name='Paused Cafe',
            slug='paused-cafe',
            whatsapp_number='919876543211',
            status='paused'
        )

        # Create category and items
        self.category = Category.objects.create(
            restaurant=self.active_restaurant,
            name='Breads',
            position=1,
            is_visible=True
        )

        self.item_avail = MenuItem.objects.create(
            restaurant=self.active_restaurant,
            category=self.category,
            name='Tandoori Roti',
            price=Decimal('20.00'),
            is_veg=True,
            is_available=True
        )

        self.item_soldout = MenuItem.objects.create(
            restaurant=self.active_restaurant,
            category=self.category,
            name='Garlic Naan',
            price=Decimal('60.00'),
            is_veg=True,
            is_available=False
        )

    def test_active_menu_renders_success(self):
        """Active restaurant should return HTTP 200 with menu and restaurant info."""
        url = reverse('public:menu', kwargs={'slug': 'test-dhaba'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public/menu.html')
        self.assertContains(response, 'Test Dhaba')
        self.assertContains(response, 'Breads')
        self.assertContains(response, 'Tandoori Roti')
        self.assertContains(response, '₹20')

    def test_table_param_prefill(self):
        """URL parameter ?table=7 should be pre-filled into the order view."""
        url = reverse('public:menu', kwargs={'slug': 'test-dhaba'}) + '?table=7'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['table_number'], '7')
        self.assertContains(response, 'Table <span x-text="tableNumber" class="ml-1 font-bold"></span>')

    def test_sold_out_item_display(self):
        """Sold out item should show 'Sold Out' marker."""
        url = reverse('public:menu', kwargs={'slug': 'test-dhaba'})
        response = self.client.get(url)
        self.assertContains(response, 'Garlic Naan')
        self.assertContains(response, 'Sold Out')

    def test_paused_restaurant_shows_friendly_notice(self):
        """Paused restaurant must return HTTP 503 and friendly paused template (Requirement C9)."""
        url = reverse('public:menu', kwargs={'slug': 'paused-cafe'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 503)
        self.assertTemplateUsed(response, 'public/paused.html')
        self.assertContains(response, 'Paused Cafe', status_code=503)
        self.assertContains(response, 'Menu Temporarily Unavailable', status_code=503)

    def test_nonexistent_restaurant_returns_404(self):
        """Invalid slug should return 404."""
        url = reverse('public:menu', kwargs={'slug': 'does-not-exist'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
