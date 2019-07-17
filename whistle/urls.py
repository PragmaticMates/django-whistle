from django.conf.urls import url
from django.utils.translation import pgettext_lazy
from whistle.views import NotificationListView, NoticeSettingsView, ReadNotificationByHashView

app_name = 'notifications'

urlpatterns = [
    url(pgettext_lazy("url", r'^settings/$'), NoticeSettingsView.as_view(), name='settings'),
    url(pgettext_lazy("url", r'^read-notification/(?P<hash>[-\w:]+)/$'), ReadNotificationByHashView.as_view(), name='read_notification'),
    url(r'^$', NotificationListView.as_view(), name='list'),
]
