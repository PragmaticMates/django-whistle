from __future__ import unicode_literals

import json
import re
import django.dispatch
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import QuerySet, Q
from django.template import loader, TemplateDoesNotExist
from django.utils.module_loading import import_string
from django.utils.timezone import now

from whistle import settings as whistle_settings


class NotificationQuerySet(QuerySet):
    def unread(self):
        return self.filter(is_read=False)

    def mark_as_read(self):
        return self.update(is_read=True)

    def for_recipient(self, recipient):
        return self.filter(recipient=recipient) if recipient.is_authenticated else self.none()

    def of_object(self, object):
        return self.filter(
            object_content_type=ContentType.objects.get_for_model(object),
            object_id=object.id
        )

    def of_target(self, target):
        return self.filter(
            target_content_type=ContentType.objects.get_for_model(target),
            target_id=target.id
        )
    
    def of_object_or_target(self, obj):
        return self.filter(
            Q(object_content_type=ContentType.objects.get_for_model(obj), object_id=obj.id) |
            Q(target_content_type=ContentType.objects.get_for_model(obj), target_id=obj.id)
        )

    def old(self, threshold=whistle_settings.OLD_THRESHOLD):
        if threshold is None:
            return self.none()

        return self.filter(created__lt=now()-threshold)

    def not_old(self, threshold=whistle_settings.OLD_THRESHOLD):
        if threshold is None:
            return self.all()

        return self.filter(created__gte=now()-threshold)


class NotificationManager(object):
    notification_emailed = django.dispatch.Signal()
    notification_pushed = django.dispatch.Signal()

    @staticmethod
    def is_channel_available(user, channel):
        return NotificationManager.is_notification_available(user, channel, event=None)

    @staticmethod
    def is_notification_available(user, channel, event):
        handler = whistle_settings.AVAILABILITY_HANDLER

        if handler:
            if isinstance(handler, str):
                handler = import_string(handler)

            channel_available = handler(user, channel, event=None)
            event_available = handler(user, channel, event)

            return channel_available and event_available

        return channel in whistle_settings.CHANNELS

    @staticmethod
    def is_channel_enabled(user, channel):
        return NotificationManager.is_notification_enabled(user, channel, event=None)

    @staticmethod
    def is_notification_enabled(user, channel, event, bypass_channel=False):
        # check if event is available for user
        if not NotificationManager.is_notification_available(user, channel, event):
            return False

        notification_settings = user.notification_settings

        # support for django-jsonfield which breaks native PostgreSQL functionality
        if isinstance(notification_settings, str):
            notification_settings = json.loads(notification_settings)

        # checking channel settings (event is empty)
        if event is None:
            try:
                # user channel setting
                return notification_settings['channels'][channel]
            except (KeyError, TypeError):
                # channel enabled by default
                return True

        # checking channel settings at first (higher priority)
        if not NotificationManager.is_channel_enabled(user, channel) and not bypass_channel:
            return False

        event_identifier = event.lower()

        try:
            # user event setting
            return notification_settings['events'][channel][event_identifier]
        except (KeyError, TypeError):
            # event enabled by default
            return True

    @staticmethod
    def notify(request, recipient, event, actor=None, object=None, target=None, details=''):
        if not recipient.is_active:
            return

        from whistle.models import Notification

        # create new notification object
        notification = Notification(
            recipient=recipient,
            event=event,
            actor=actor,
            object=object,
            target=target,
            details=details
        )

        # web
        if NotificationManager.is_notification_enabled(recipient, 'web', event):
            # save notification to DB
            notification.save()

            # clear user notifications cache
            recipient.clear_unread_notifications_cache()

        # email
        if NotificationManager.is_notification_enabled(recipient, 'email', event):
            notification.send_mail(request)
            NotificationManager.notification_emailed.send(
                sender=NotificationManager, notification=notification, request=request,
            )

        # push
        if NotificationManager.is_notification_enabled(recipient, 'push', event):
            notification.push(request)
            NotificationManager.notification_pushed.send(
                sender=NotificationManager, notification=notification,
            )

    @staticmethod
    def get_description(event, actor, object, target, pass_variables=True):
        event_template = dict(whistle_settings.EVENTS).get(event)

        event_context = {
            'actor': actor if actor else '',
            'object': object if object else '',
            'target': target if target else '',
        } if pass_variables else {
            'actor': '',
            'object': '',
            'target': '',
        }

        if object:
            object_content_type = ContentType.objects.get_for_model(object)
            event_context[object_content_type.model.lower()] = object if pass_variables else ''

        if target:
            target_content_type = ContentType.objects.get_for_model(target)
            event_context[target_content_type.model.lower()] = target if pass_variables else ''

        description = event_template % event_context

        # TODO: move to another static method (helper)
        description = description.replace("''", '')   # remove all 2 single quotas
        description = description.replace('""', '')   # remove all 2 double quotas
        description = description.replace('()', '')   # remove empty braces
        description = description.strip(' :.')        # remove trailing spaces and semicolons
        description = re.sub(' +', ' ', description)  # remove all multiple spaces

        return description


class EmailManager(object):
    @staticmethod
    def send_mail(notification, request):
        """
        Send email notification about a new event to its recipient
        """

        html_message, message, recipient_list, subject = EmailManager.prepare_email(notification, request)

        if whistle_settings.USE_RQ:
            # use background task to release main thread
            from whistle.helpers import send_mail_in_background
            send_mail_in_background.delay(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)
        else:
            # send mail in main thread
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)

    # TODO: Improve
    @staticmethod
    def prepare_email(notification, request):
        # template
        try:
            t = loader.get_template('whistle/mails/{}.txt'.format(notification.event.lower()))
        except TemplateDoesNotExist:
            t = loader.get_template('whistle/mails/new_notification.txt'.format(notification.event.lower()))

        # HTML template
        try:
            t_html = loader.get_template('whistle/mails/{}.html'.format(notification.event.lower()))
        except TemplateDoesNotExist:
            try:
                t_html = loader.get_template('whistle/mails/new_notification.html')
            except TemplateDoesNotExist:
                t_html = None

        # recipients
        recipient_list = [notification.recipient.email]

        # description
        description = NotificationManager.get_description(notification.event, notification.actor, notification.object, notification.target, True)

        # subject
        short_description = NotificationManager.get_description(notification.event, notification.actor, notification.object, notification.target, False)

        try:
            site = get_current_site(request)

            subject = '[{}] {}'.format(
                site.name,
                short_description  # TODO: add setting if short or long description should be used in subject
            )
        except ObjectDoesNotExist:
            subject = short_description

        # context
        context = {
            'subject': subject,
            'description': description,
            'short_description': short_description,
            'request': request,
            'recipient': notification.recipient,
            'actor': notification.actor,
            'object': notification.object,
            'target': notification.target,
            'details': notification.details,
            'event': notification.event,
            'hash': notification.hash,
            'url': notification.get_absolute_url(),
            'settings': settings
        }

        if notification.object:
            object_content_type = ContentType.objects.get_for_model(notification.object)
            context[object_content_type.model.lower()] = notification.object

        if notification.target:
            target_content_type = ContentType.objects.get_for_model(notification.target)
            context[target_content_type.model.lower()] = notification.target

        # message
        message = t.render(context)

        # HTML
        html_message = t_html.render(context) if t_html else None

        return html_message, message, recipient_list, subject
