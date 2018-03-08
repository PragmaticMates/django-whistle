from django.core.exceptions import ObjectDoesNotExist
from whistle.models import Notification


class ReadNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            notification_id = request.GET.get('read-notification', None)

            if notification_id:
                try:
                    notification = Notification.objects.get(pk=notification_id, is_read=False)

                    if notification.recipient == request.user:
                        notification.is_read = True
                        notification.save(update_fields=['is_read'])
                        print('save')
                        request.user.clear_unread_notifications_cache()
                except ObjectDoesNotExist:
                    pass

        return self.get_response(request)
