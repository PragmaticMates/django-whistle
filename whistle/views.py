from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, FormView
from whistle.forms import EditNoticesForm
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


class NoticeSettingsView(LoginRequiredMixin, FormView):
    form_class = EditNoticesForm
    success_url = '/'
    template_name = 'whistle/settings.html'

    def form_valid(self, form):
        # update user notices settings
        user = self.request.user
        user.notices_settings = form.cleaned_data
        user.save(update_fields=['notices_settings'])
        messages.success(self.request, _('Notices settings successfully updated'))
        return super(NoticeSettingsView, self).form_valid(form)

    def get_form_kwargs(self):
        form_kwargs = super(NoticeSettingsView, self).get_form_kwargs()
        form_kwargs['user'] = self.request.user
        return form_kwargs
