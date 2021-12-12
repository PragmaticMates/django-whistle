from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT

EVENTS = getattr(settings, 'WHISTLE_NOTIFICATION_EVENTS', [])
URL_HANDLER = getattr(settings, 'WHISTLE_URL_HANDLER', None)
TIMEOUT = getattr(settings, 'WHISTLE_CACHE_TIMEOUT', DEFAULT_TIMEOUT)
USE_RQ = getattr(settings, 'WHISTLE_USE_RQ', True)
REDIS_QUEUE = getattr(settings, 'WHISTLE_REDIS_QUEUE', 'default')
SIGNING_KEY = getattr(settings, 'WHISTLE_SIGNING_KEY', settings.SECRET_KEY)
SIGNING_SALT = getattr(settings, 'WHISTLE_SIGNING_SALT', 'whistle')
AUTH_USER_MODEL = getattr(settings, 'WHISTLE_AUTH_USER_MODEL', settings.AUTH_USER_MODEL)
PUSH_NOTIFICATIONS_ENABLED = 'fcm_django' in settings.INSTALLED_APPS
