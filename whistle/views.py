from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import BadSignature
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import ListView, FormView

from whistle import settings
from whistle.forms import NotificationSettingsForm
from whistle.models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.user.notifications.unread().mark_as_read()
            request.user.clear_unread_notifications_cache()
        return super(NotificationListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.notifications.select_related('actor', 'recipient')


class NotificationSettingsView(LoginRequiredMixin, FormView):
    form_class = NotificationSettingsForm
    success_url = reverse_lazy('notifications:settings')  # TODO: configurable
    template_name = 'whistle/settings.html'

    def form_valid(self, form):
        user = self.request.user
        user.notification_settings = form.cleaned_data
        user.save(update_fields=['notification_settings'])
        messages.success(self.request, _('Notification settings successfully updated'))
        return super(NotificationSettingsView, self).form_valid(form)

    def get_form_kwargs(self):
        form_kwargs = super(NotificationSettingsView, self).get_form_kwargs()
        form_kwargs['user'] = self.request.user
        return form_kwargs


class ReadNotificationByHashView(View):
    def dispatch(self, *args, **kwargs):
        hash = kwargs.get('hash')

        from django.core import signing

        try:
            notification_data = signing.loads(hash, key=settings.SIGNING_KEY, salt=settings.SIGNING_SALT)
        except BadSignature:
            return HttpResponse('BAD SIGNATURE')

        notification_id = notification_data.get('notification_id', None)
        recipient_id = notification_data.get('recipient_id', None)

        try:
            notification = Notification.objects.get(pk=notification_id)

            if notification.is_read:
                return HttpResponse('ALREADY READ')

            user = get_user_model().objects.get(pk=recipient_id)

            if notification.recipient != user:
                return HttpResponse('INVALID RECIPIENT')

            notification.is_read = True
            notification.save(update_fields=['is_read'])
            user.clear_unread_notifications_cache()

        except ObjectDoesNotExist:
            return HttpResponse('NOT FOUND')

        return HttpResponse('OK')
