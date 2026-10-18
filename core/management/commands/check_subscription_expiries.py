from django.core.management.base import BaseCommand
from django.utils import timezone
from billing.models import Subscription


class Command(BaseCommand):
    help = 'Checks for expired subscriptions and auto-pauses restaurants on lapse'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_count = 0

        # Subscriptions currently trialing or active whose period/trial has expired
        subs = Subscription.objects.filter(status__in=['trialing', 'active']).select_related('restaurant')

        for sub in subs:
            if not sub.is_valid:
                sub.status = 'expired'
                sub.save(update_fields=['status'])

                restaurant = sub.restaurant
                if restaurant.status == 'active':
                    restaurant.status = 'paused'
                    restaurant.save(update_fields=['status'])
                    self.stdout.write(f"Auto-paused lapsed restaurant: {restaurant.name} (id: {restaurant.id})")
                    expired_count += 1

        self.stdout.write(self.style.SUCCESS(f"Subscription expiry check complete. {expired_count} restaurants auto-paused."))
