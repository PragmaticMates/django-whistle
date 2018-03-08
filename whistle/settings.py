from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT

EVENTS = getattr(settings, 'WHISTLE_NOTIFICATION_EVENTS', [])
TIMEOUT = getattr(settings, 'WHISTLE_CACHE_TIMEOUT', DEFAULT_TIMEOUT)
USE_RQ = getattr(settings, 'WHISTLE_USE_RQ', True)
