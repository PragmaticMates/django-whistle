from django.conf.urls import url
from django.utils.translation import pgettext_lazy
from whistle.views import NotificationListView, NoticeSettingsView

app_name = 'notifications'

urlpatterns = [
    url(r'^$', NotificationListView.as_view(), name='list'),
    url(pgettext_lazy("url", r'^settings/$'), NoticeSettingsView.as_view(), name='settings'),
]
