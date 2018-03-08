from django.core.mail import send_mail
from whistle.managers import NoticeManager


def notify(request, recipient, event, actor=None, object=None, target=None):
    NoticeManager.notify(request, recipient, event, actor, object, target)



from django_rq import job
@job
def send_mail_in_background(subject, message, from_email, recipient_list, fail_silently=True):
    send_mail(subject, message, from_email, recipient_list, fail_silently)
