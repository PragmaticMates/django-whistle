from django.contrib.postgres.fields import JSONField
from django.core.cache import cache
from django.db import models
from whistle import settings as whistle_settings


class UserNotificationsMixin(models.Model):
    notices_settings = JSONField(blank=True, null=True, default=None)

    class Meta:
        abstract = True

    @property
    def unread_notifications(self):
        cache_key = 'user_unread_notifications'
        cache_version = self.pk
        saved_notifications = cache.get(cache_key, version=cache_version)

        if saved_notifications is not None:
            return saved_notifications

        unread_notifications = self.notifications.unread()

        for notification in unread_notifications:
            if notification.object:
                notification.object_display = str(notification.object)
                notification.object_url = notification.object.get_absolute_url()
                notification.object_model = notification.object.__class__.__name__

            if notification.target:
                notification.target_display = str(notification.target)
                notification.target_url = notification.target.get_absolute_url()
                notification.target_model = notification.target.__class__.__name__

        # save into cache
        cache.set(cache_key, unread_notifications, version=cache_version, timeout=whistle_settings.TIMEOUT)

        return unread_notifications

    def clear_unread_notifications_cache(self):
        cache_key = 'user_unread_notifications'
        cache.delete(cache_key, version=self.pk)
