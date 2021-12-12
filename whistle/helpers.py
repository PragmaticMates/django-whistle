from django_rq import job
from django.core.mail import send_mail
from whistle.managers import NotificationManager
from whistle import settings as whistle_settings


def notify(request, recipient, event, actor=None, object=None, target=None, details=''):
    NotificationManager.notify(request, recipient, event, actor, object, target, details)


@job(whistle_settings.REDIS_QUEUE)
def send_mail_in_background(subject, message, from_email, recipient_list, html_message=None, fail_silently=True):
    send_mail(subject, message, from_email, recipient_list, html_message=html_message, fail_silently=fail_silently)
