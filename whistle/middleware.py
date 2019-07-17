from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView

from whistle.models import Notification


class ReadNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # read notification by its id
            notification_id = request.GET.get('read-notification', None)

            if notification_id:
                try:
                    notification = Notification.objects.get(pk=notification_id, is_read=False)

                    if notification.recipient == request.user:
                        notification.is_read = True
                        notification.save(update_fields=['is_read'])
                        request.user.clear_unread_notifications_cache()
                except ObjectDoesNotExist:
                    pass

        # read notifications by context
        response = self.get_response(request)
        reload_response = False

        try:
            context = response.context_data
            view = context.get('view')

            if isinstance(view, DetailView):
                # read notifications by object
                object = context.get('object')

                unread_notifications = Notification.objects\
                    .unread()\
                    .for_recipient(request.user)\
                    .of_object_or_target(object)

                if unread_notifications.exists():
                    unread_notifications.update(is_read=True)
                    request.user.clear_unread_notifications_cache()
                    reload_response = True

        except AttributeError:
            pass

        if reload_response:
            response = self.get_response(request)

        return response
