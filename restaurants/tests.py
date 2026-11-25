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


class GeofencePolygonTests(TestCase):
    def setUp(self):
        # A simple square ~ 20m x 20m centered near 26.4584, 84.4420
        # 1 deg lat ~= 111,320m -> 0.0001 deg ~= 11.1m
        self.polygon = [
            {'lat': 26.4585, 'lng': 84.4420},  # NW
            {'lat': 26.4585, 'lng': 84.4422},  # NE
            {'lat': 26.4583, 'lng': 84.4422},  # SE
            {'lat': 26.4583, 'lng': 84.4420},  # SW
        ]

    def test_point_inside(self):
        from restaurants.utils import is_point_inside_polygon
        # Center of square
        self.assertTrue(is_point_inside_polygon(26.4584, 84.4421, self.polygon))

    def test_point_far_outside(self):
        from restaurants.utils import is_point_inside_polygon
        # Point ~25m to the east (approx 84.44245)
        self.assertFalse(is_point_inside_polygon(26.4584, 84.4425, self.polygon, tolerance_meters=5.0))

    def test_point_within_5m_edge(self):
        from restaurants.utils import is_point_inside_polygon
        # Point very slightly outside the eastern edge (84.442202 -> ~0.2m outside)
        self.assertTrue(is_point_inside_polygon(26.4584, 84.442203, self.polygon, tolerance_meters=5.0))

