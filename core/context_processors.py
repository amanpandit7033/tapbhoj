import time
from django.conf import settings


def static_version(request):
    """
    Cache-busting context processor.
    In DEBUG mode, returns current timestamp so browsers never use stale cached CSS.
    In production, returns fixed release version.
    """
    version = int(time.time()) if settings.DEBUG else getattr(settings, 'APP_VERSION', '1.0.0')
    return {
        'STATIC_VERSION': version,
    }
