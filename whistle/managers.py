from __future__ import unicode_literals

import json
import django.dispatch
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q
from django.template import loader, TemplateDoesNotExist
from django.utils.module_loading import import_string
from django.utils.timezone import now
from pragmatic.helpers import method_overridden

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

    def is_channel_available(self, user, channel):
        return self.is_notification_available(user, channel, event=None)

    def is_notification_available(self, user, channel, event):
        handler = whistle_settings.AVAILABILITY_HANDLER

        if handler:
            if isinstance(handler, str):
                handler = import_string(handler)

            channel_available = handler(user, channel, event=None)
            event_available = handler(user, channel, event)

            return channel_available and event_available

        return channel in whistle_settings.CHANNELS

    def is_channel_enabled(self, user, channel):
        return self.is_notification_enabled(user, channel, event=None)

    def is_notification_enabled(self, user, channel, event, bypass_channel=False):
        # check if event is available for user
        if not self.is_notification_available(user, channel, event):
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
        if not self.is_channel_enabled(user, channel) and not bypass_channel:
            return False

        event_identifier = event.lower()

        try:
            # user event setting
            return notification_settings['events'][channel][event_identifier]
        except (KeyError, TypeError):
            # event enabled by default
            return True

    def notify(self, recipient, event, actor=None, object=None, target=None, details=''):
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
        if self.is_notification_enabled(recipient, 'web', event):
            # save notification to DB
            notification.save()

            # clear user notifications cache
            recipient.clear_unread_notifications_cache()

        # email
        if self.is_notification_enabled(recipient, 'email', event):
            notification.send_mail()
            self.notification_emailed.send(
                sender=self.__class__, notification=notification,
            )

        # push
        if self.is_notification_enabled(recipient, 'push', event):
            notification.push()
            self.notification_pushed.send(
                sender=self.__class__, notification=notification,
            )

    def get_event_context(self, event, actor, object, target):
        event_context = {
            'actor': actor if actor else '',
            'object': object if object else '',
            'target': target if target else '',
        }

        if object:
            object_content_type = ContentType.objects.get_for_model(object)
            event_context[object_content_type.model.lower()] = object

        if target:
            target_content_type = ContentType.objects.get_for_model(target)
            event_context[target_content_type.model.lower()] = target

        return event_context

    def get_description(self, event, actor, object, target, pass_variables=True):
        event_context = self.get_event_context(
            event=event,
            actor=actor,
            object=object,
            target=target
        )

        if not pass_variables:
            for key in event_context:
                event_context[key] = ''

        event_template = dict(whistle_settings.EVENTS).get(event)
        description = event_template % event_context

        # strip unwanted or duplicated characters
        from whistle.helpers import strip_unwanted_chars
        description = strip_unwanted_chars(description)

        return description

    def mail_notification(self, notification):
        from whistle.settings import email_manager

        return email_manager.send_mail(
            recipient=notification.recipient,
            event=notification.event,
            actor=notification.actor,
            object=notification.object,
            target=notification.target,
            details=notification.details,
            hash=notification.hash,
            url=notification.get_absolute_url()
        )

    def get_push_config(self, notification):
        if notification.details not in EMPTY_VALUES:
            title = notification.description
            body = notification.details
        elif method_overridden(notification.object, '__repr__'):
            title = notification.short_description()
            body = repr(notification.object) if notification.object else ''
        else:
            title = notification.short_description()
            body = str(notification.object) if notification.object else ''

        return {
            'title': title,
            'body': body,
            # 'image_url': TODO,
            'android': {
                'collapse_key': f'{notification.event}_{notification.object_id}',
                'priority': 'high',
                'click_action': notification.event,
                'sound': 'default'
            },
            'apns': {
                'category': notification.event,
                'sound': 'default'
            }
        }

    def push_notification(self, notification):
        from fcm_django.models import FCMDevice
        from firebase_admin.messaging import Notification, Message, \
            AndroidConfig, AndroidNotification, APNSPayload, Aps, APNSConfig

        for device in notification.recipient.fcmdevice_set.filter(active=True):
            data = {}
            for data_attr in ['id', 'object_id', 'target_id', 'object_content_type', 'target_content_type']:
                value = getattr(notification, data_attr)

                if value:
                    data[data_attr] = '.'.join(value.natural_key()) if isinstance(value, ContentType) else str(value)

            # from objprint import op
            # op(data)

            result = device.send_message(
                Message(
                    notification=Notification(
                        title=notification.push_config['title'],
                        body=notification.push_config['body'],
                        # image=self.push_data['image_url']"
                    ),
                    data=data,
                    android=AndroidConfig(
                        collapse_key=notification.push_config['android']['collapse_key'],
                        priority=notification.push_config['android']['priority'],
                        notification=AndroidNotification(
                            click_action=notification.push_config['android']['click_action'],
                            sound=notification.push_config['android']['sound']
                        )
                    ),
                    apns=APNSConfig(
                        payload=APNSPayload(
                            aps=Aps(
                                badge=notification.recipient.unread_notifications_count,
                                category=notification.push_config['apns']['category'],
                                sound=notification.push_config['apns']['sound']
                            )
                        )
                    )
                )
            )
            # op(result)

            return result


class EmailManager(object):
    def send_mail(self, recipient, event, **kwargs):
        """
        Send email notification about a new event to its recipient
        """

        html_message, message, recipient_list, subject = self.prepare_email(
            recipient=recipient,
            event=event,
            **kwargs
        )

        if whistle_settings.USE_RQ:
            # use background task to release main thread
            from whistle.jobs import send_mail_in_background
            send_mail_in_background.delay(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)
        else:
            # send mail in main thread
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)

    def load_template(self, template_type, recipient, event, **kwargs):
        try:
            # event specific template
            return (
                loader.get_template('whistle/mails/{}.{}'.format(event.lower(), template_type)),
                False
            )
        except TemplateDoesNotExist:
            try:
                # default universal template
                return (
                    loader.get_template('whistle/mails/new_notification.{}'.format(template_type)),
                    True
                )
            except TemplateDoesNotExist:
                return (
                    None,
                    None
                )

    def prepare_email(self, recipient, event, **kwargs):
        # Load templates
        t, _ = self.load_template("txt", recipient, event, **kwargs)
        t_html, _ = self.load_template("html", recipient, event, **kwargs)

        # recipients
        recipient_list = [recipient.email]

        # context
        context = self.get_mail_context(recipient, event, **kwargs)

        # subject
        subject = self.get_mail_subject(context)

        # message
        message = t.render(context)

        # HTML
        html_message = t_html.render(context) if t_html else None

        return html_message, message, recipient_list, subject

    def get_mail_subject(self, context):
        try:
            site = get_current_site(request=None)

            return '[{}] {}'.format(
                site.name,
                context['short_description']
            )
        except ObjectDoesNotExist:
            return context['short_description']

    def get_mail_context(self, recipient, event, **kwargs):
        actor = kwargs.get('actor', None)
        object = kwargs.get('object', None)
        target = kwargs.get('target', None)

        description_kwargs = {
            'event': event,
            'actor': actor,
            'object': object,
            'target': target
        }

        # descriptions and subject
        from whistle.settings import notification_manager
        description = notification_manager.get_description(**description_kwargs, pass_variables=True)
        short_description = notification_manager.get_description(**description_kwargs, pass_variables=False)

        context = kwargs

        context.update({
            'recipient': recipient,
            'event': event,
            'description': description,
            'short_description': short_description,
            'settings': settings,
        })

        if object:
            object_content_type = ContentType.objects.get_for_model(object)
            context[object_content_type.model.lower()] = object

        if target:
            target_content_type = ContentType.objects.get_for_model(target)
            context[target_content_type.model.lower()] = target

        return context
