from django_rq import job
from django.core.mail import send_mail
from whistle import settings as whistle_settings


@job(whistle_settings.REDIS_QUEUE)
def notify_in_background(recipient, event, actor=None, object=None, target=None, details=''):
    notify(recipient=recipient, event=event, actor=actor, object=object, target=target, details=details)


@job(whistle_settings.REDIS_QUEUE)
def send_mail_in_background(subject, message, from_email, recipient_list, html_message=None, fail_silently=True):
    send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list,
              html_message=html_message, fail_silently=fail_silently)
