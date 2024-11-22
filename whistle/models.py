from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models
from django.utils.module_loading import import_string
from django.utils.translation import gettext, gettext_lazy as _, get_language

import urllib.parse as urlparse
from urllib.parse import urlencode

from whistle import settings as whistle_settings
from whistle.managers import NotificationQuerySet
from whistle.settings import notification_manager


class Notification(models.Model):
    recipient = models.ForeignKey(whistle_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    event = models.CharField(_('event'), choices=whistle_settings.EVENTS, max_length=50, db_index=True)
    actor = models.ForeignKey(whistle_settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
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

    @property
    def hash(self):
        from django.core import signing
        protect = {'notification_id': self.pk, 'recipient_id': self.recipient.pk}
        return signing.dumps(protect, key=whistle_settings.SIGNING_KEY, salt=whistle_settings.SIGNING_SALT)

    def short_description(self):
        return self.get_description(False)

    def get_description(self, pass_variables, bypass_cache=False):
        language = get_language()

        cache_key = self.__class__.__name__.lower()
        cache_version = '{}_{}_{}'.format(self.pk, language, pass_variables)
        saved_description = cache.get(cache_key, version=cache_version)

        if saved_description is not None and not bypass_cache:
            return saved_description

        try:
            description = notification_manager.get_description(self.event, self.actor, self.object, self.target, pass_variables)
        except KeyError:
            # if self.pk:
            #     self.delete()
            return gettext('Failed to retrieve description')

        # save into cache
        cache.set(cache_key, description, version=cache_version, timeout=whistle_settings.TIMEOUT)

        return description

    def resave_description(self):
        return {
            'long': self.get_description(pass_variables=True, bypass_cache=True),
            'short': self.get_description(pass_variables=False, bypass_cache=True),
        }

    def get_absolute_url(self):
        language = get_language()
        cache_key = 'notification_url'
        cache_version = '{}_{}'.format(self.pk, language)
        saved_url = cache.get(cache_key, version=cache_version)

        if saved_url is not None:
            return saved_url

        url = '#'
        for obj in [self.object, self.target]:
            try:
                url = '#' if obj is None else obj.get_absolute_url()
                break
            except:
                continue

        url_handler = whistle_settings.URL_HANDLER

        if url_handler:
            if isinstance(url_handler, str):
                url_handler = import_string(url_handler)

            url = url_handler(url, self)

        if not self.is_read:
            # add read-notification param for middleware
            params = {whistle_settings.URL_PARAM: self.pk}
            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlencode(query)
            url = urlparse.urlunparse(url_parts)

        # save into cache
        cache.set(cache_key, url, version=cache_version, timeout=whistle_settings.TIMEOUT)

        return url

    @property
    def push_config(self):
        return notification_manager.get_push_config(
            notification=self
        )

    def send_mail(self):
        return notification_manager.mail_notification(
            notification=self,
        )

    def push(self):
        return notification_manager.push_notification(
            notification=self
        )
