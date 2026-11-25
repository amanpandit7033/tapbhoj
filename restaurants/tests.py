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

