from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _, ngettext
from whistle.forms import NotificationAdminForm
from whistle.managers import EmailManager
from whistle.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    actions = ['make_unread', 'make_read', 'clear_unread_notifications_cache', 'send_email', 'push']
    date_hierarchy = 'created'
    list_select_related = ('recipient', 'actor')
    list_display = ('__str__', 'recipient', 'actor', 'is_read', 'created')
    list_filter = ('event', 'is_read')
    raw_id_fields = ('recipient', 'actor')
    form = NotificationAdminForm

    def make_unread(self, request, queryset):
        rows_updated = queryset.update(is_read=False)

        message = ngettext(
            '%(count)d notification was marked as unread',
            '%(count)d notifications were marked as unread',
            rows_updated
        ) % {
            'count': rows_updated,
        }

        self.message_user(request, message)
    make_unread.short_description = _('Make unread')

    def make_read(self, request, queryset):
        rows_updated = queryset.update(is_read=True)

        message = ngettext(
            '%(count)d notification was marked as read',
            '%(count)d notifications were marked as read',
            rows_updated
        ) % {
            'count': rows_updated,
        }

        self.message_user(request, message)
    make_read.short_description = _('Make read')

    def clear_unread_notifications_cache(self, request, queryset):
        recipients = get_user_model().objects.filter(pk__in=queryset.values_list('recipient', flat=True))

        if recipients.exists():
            for recipient in recipients:
                recipient.clear_unread_notifications_cache()
            self.message_user(request, _('Unread notifications cache cleared'))
    clear_unread_notifications_cache.short_description = _('Clear unread notifications cache')

    def send_email(self, request, queryset):
        for notification in queryset:
            notification.send_mail(request)
    send_email.short_description = _('Send email')

    def push(self, request, queryset):
        for notification in queryset:
            notification.push(request)
    push.short_description = _('Push')
