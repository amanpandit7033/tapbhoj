from django.test import TestCase
from django.urls import reverse

class Phase0SetupTests(TestCase):
    def test_homepage_status_and_template(self):
        """Verify the base verification page loads with HTTP 200 and renders base templates."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'TapBhoj')
        self.assertContains(response, 'Phase 0 Ready')
