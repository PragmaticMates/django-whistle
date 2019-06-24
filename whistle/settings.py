from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT

EVENTS = getattr(settings, 'WHISTLE_NOTIFICATION_EVENTS', [])
URL_HANDLER = getattr(settings, 'WHISTLE_URL_HANDLER', None)
TIMEOUT = getattr(settings, 'WHISTLE_CACHE_TIMEOUT', DEFAULT_TIMEOUT)
USE_RQ = getattr(settings, 'WHISTLE_USE_RQ', True)
REDIS_QUEUE = getattr(settings, 'WHISTLE_REDIS_QUEUE', 'default')
