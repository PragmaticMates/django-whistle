from django.urls import re_path
from django.utils.translation import pgettext_lazy
from whistle.views import NotificationListView, NotificationSettingsView, ReadNotificationByHashView

app_name = 'notifications'

urlpatterns = [
    re_path(pgettext_lazy("url", r'^settings/$'), NotificationSettingsView.as_view(), name='settings'),
    re_path(pgettext_lazy("url", r'^read-notification/(?P<hash>[-\w:]+)/$'), ReadNotificationByHashView.as_view(), name='read_notification'),
    re_path(r'^$', NotificationListView.as_view(), name='list'),
]
