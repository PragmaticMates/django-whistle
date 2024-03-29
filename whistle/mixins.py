try:
    # Django 3.1
    from django.db.models import JSONField
except ImportError:
    # older Django
    from django.contrib.postgres.fields import JSONField

from django.core.cache import cache
from django.db import models
from whistle import settings as whistle_settings


class UserNotificationsMixin(models.Model):
    CACHE_KEY = 'user_unread_notifications'

    notification_settings = JSONField(blank=True, null=True, default=None)

    class Meta:
        abstract = True

    @property
    def unread_notifications_count(self):
        cache_key = self.CACHE_KEY
        cache_version = self.pk

        try:
            saved_unread_notifications = cache.get(cache_key, version=cache_version)
            if saved_unread_notifications is not None:
                # return saved_unread_notifications.count()
                return len(saved_unread_notifications)
        except LookupError:
            pass

        return self.notifications.unread().count()

    @property
    def unread_notifications(self):
        cache_key = self.CACHE_KEY
        cache_version = self.pk

        try:
            saved_notifications = cache.get(cache_key, version=cache_version)
        except LookupError:
            # app models could change
            saved_notifications = None

        if saved_notifications is not None:
            return saved_notifications

        unread_notifications = self.notifications.unread().select_related('actor')

        for notification in unread_notifications:
            if notification.object:
                notification.object_display = str(notification.object)

                try:
                    notification.object_url = notification.object.get_absolute_url()
                except AttributeError:
                    notification.object_url = '#'

                notification.object_model = notification.object.__class__.__name__

            if notification.target:
                notification.target_display = str(notification.target)

                try:
                    notification.target_url = notification.target.get_absolute_url()
                except AttributeError:
                    notification.target_url = '#'

                notification.target_model = notification.target.__class__.__name__

        # save into cache
        cache.set(cache_key, unread_notifications, version=cache_version, timeout=whistle_settings.TIMEOUT)

        return unread_notifications

    def clear_unread_notifications_cache(self):
        cache_key = self.CACHE_KEY
        cache.delete(cache_key, version=self.pk)
