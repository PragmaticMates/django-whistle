from __future__ import unicode_literals

import json
import re
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.template import loader, TemplateDoesNotExist

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


class NoticeManager(object):
    @staticmethod
    def is_notice_allowed(user, channel, event):
        event_identifier = event.lower()

        notices_settings = user.notices_settings

        # support for django-jsonfield which breaks native PostgreSQL functionality
        if isinstance(notices_settings, str):
            notices_settings = json.loads(notices_settings)

        try:
            return notices_settings[channel][event_identifier]
        except (KeyError, TypeError):
            return True

    @staticmethod
    def notify(request, recipient, event, actor=None, object=None, target=None, details=''):
        registered_for_notification = NoticeManager.is_notice_allowed(recipient, 'notification', event)

        if registered_for_notification:
            from whistle.models import Notification

            # create new notification object
            notification = Notification.objects.create(
                recipient=recipient,
                event=event,
                actor=actor,
                object=object,
                target=target,
                details=details
            )

            # clear user notifications cache
            recipient.clear_unread_notifications_cache()

        registered_for_email = NoticeManager.is_notice_allowed(recipient, 'mail', event)

        if registered_for_email:
            EmailManager.send_mail(request, recipient, event, actor, object, target, details)

    @staticmethod
    def get_description(event, actor, object, target, pass_variables=True):
        event_template = dict(whistle_settings.EVENTS).get(event)

        event_context = {
            'actor': actor,
            'object': object,
            'target': target,
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

        if not pass_variables:
            description = description.replace("''", '')   # remove all 2 single quotas
            description = description.replace('""', '')   # remove all 2 double quotas
            description = re.sub(' +', ' ', description)  # remove all multiple spaces
            description = description.strip(' :')         # remove trailing spaces and semicolons
        return description


class EmailManager(object):
    @staticmethod
    def send_mail(request, recipient, event, actor=None, object=None, target=None, details=''):
        """
        Send email notification about a new event to its recipient
        """

        # template
        try:
            t = loader.get_template('whistle/mails/{}.txt'.format(event.lower()))
        except TemplateDoesNotExist:
            t = loader.get_template('whistle/mails/new_notification.txt'.format(event.lower()))

        # HTML template
        try:
            t_html = loader.get_template('whistle/mails/{}.html'.format(event.lower()))
        except TemplateDoesNotExist:
            try:
                t_html = loader.get_template('whistle/mails/new_notification.html')
            except TemplateDoesNotExist:
                t_html = None

        # recipients
        recipient_list = [recipient.email]

        # description
        description = NoticeManager.get_description(event, actor, object, target, True)

        # subject
        short_description = NoticeManager.get_description(event, actor, object, target, False)

        site = get_current_site(request)

        subject = '[{}] {}'.format(
            site.name,
            short_description  # TODO: add setting if short or long description should be used in subject
        )

        # context
        context = {
            'subject': subject,
            'description': description,
            'short_description': short_description,
            'request': request,
            'recipient': recipient,
            'actor': actor,
            'object': object,
            'target': target,
            'event': event,
        }

        if object:
            object_content_type = ContentType.objects.get_for_model(object)
            context[object_content_type.model.lower()] = object

        if target:
            target_content_type = ContentType.objects.get_for_model(target)
            context[target_content_type.model.lower()] = target

        # message
        message = t.render(context)

        # HTML
        if t_html:
            html_message = t_html.render(context)
        else:
            html_message = None

        if whistle_settings.USE_RQ:
            # use background task to release main thread
            from whistle.helpers import send_mail_in_background
            send_mail_in_background.delay(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)
        else:
            # send mail in main thread
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)
