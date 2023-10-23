import re
from django_rq import job
from django.core.mail import send_mail
from whistle import settings as whistle_settings
from whistle.settings import NotificationManager


def notify(request, recipient, event, actor=None, object=None, target=None, details=''):
    NotificationManager.notify(request, recipient, event, actor, object, target, details)


@job(whistle_settings.REDIS_QUEUE)
def notify_in_background(request, recipient, event, actor=None, object=None, target=None, details=''):
    notify(request, recipient, event, actor=actor, object=object, target=target, details=details)


@job(whistle_settings.REDIS_QUEUE)
def send_mail_in_background(subject, message, from_email, recipient_list, html_message=None, fail_silently=True):
    send_mail(subject, message, from_email, recipient_list, html_message=html_message, fail_silently=fail_silently)


def strip_unwanted_chars(str):
    str = str.replace("''", '')  # remove all 2 single quotas
    str = str.replace('""', '')  # remove all 2 double quotas
    str = str.replace('()', '')  # remove empty braces
    str = str.strip(' :.')  # remove trailing spaces and semicolons
    str = re.sub(' +', ' ', str)  # remove all multiple spaces
    return str
