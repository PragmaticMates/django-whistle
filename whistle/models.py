from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy as _, get_language, ugettext
from whistle.managers import NotificationQuerySet, NoticeManager
from whistle import settings as whistle_settings

try:
    # Python 2
    import urlparse
    from urllib import urlencode
except:
    # Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    event = models.CharField(_('event'), choices=whistle_settings.EVENTS, max_length=32, db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        blank=True, null=True, default=None)

    object_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='notification_object',
        blank=True, null=True, default=None)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    object = GenericForeignKey(ct_field='object_content_type', fk_field='object_id')

    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='notification_target',
        blank=True, null=True, default=None)
    target_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    target = GenericForeignKey(ct_field='target_content_type', fk_field='target_id')

    details = models.TextField(_('details'), blank=True, default='')
    is_read = models.BooleanField(_('read'), default=False, db_index=True)
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    objects = NotificationQuerySet.as_manager()

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ('-created',)

    def __str__(self):
        return self.description

    @property
    def description(self):
        return self.get_description(True)

    def short_description(self):
        return self.get_description(False)

    def get_description(self, pass_variables):
        language = get_language()

        cache_key = self.__class__.__name__.lower()
        cache_version = '{}_{}_{}'.format(self.pk, language, pass_variables)
        saved_description = cache.get(cache_key, version=cache_version)

        if saved_description is not None:
            return saved_description

        try:
            description = NoticeManager.get_description(self.event, self.actor, self.object, self.target, pass_variables)
        except KeyError:
            # referenced object does not exist anymore
            if self.pk:
                self.delete()
            return ugettext('Related object does not exist anymore')

        # save into cache
        cache.set(cache_key, description, version=cache_version, timeout=whistle_settings.TIMEOUT)

        return description

    def get_absolute_url(self):
        language = get_language()
        cache_key = 'notification_url'
        cache_version = '{}_{}'.format(self.pk, language)
        saved_url = cache.get(cache_key, version=cache_version)

        if saved_url is not None:
            return saved_url

        try:
            url = '#' if self.object is None else self.object.get_absolute_url()
        except AttributeError:
            url = '#' if self.target is None else self.target.get_absolute_url()

        if not self.is_read:
            # add read-notification param for middleware
            params = {'read-notification': self.pk}
            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlencode(query)
            url = urlparse.urlunparse(url_parts)

        # save into cache
        cache.set(cache_key, url, version=cache_version, timeout=whistle_settings.TIMEOUT)

        return url
