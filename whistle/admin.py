from django.contrib import admin, messages
from django.contrib.auth import get_user_model

try:
    # older Django
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    # Django >= 3
    from django.utils.translation import gettext_lazy as _

from django.utils.translation import ngettext

from whistle import settings as whistle_settings
from whistle.forms import NotificationAdminForm
from whistle.models import Notification


class OldListFilter(admin.SimpleListFilter):
    title = _('old')
    parameter_name = 'old'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('yes')),
            ('no', _('no')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.old()

        if self.value() == 'no':
            return queryset.not_old()

        return queryset


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    actions = ['make_unread', 'make_read', 'clear_unread_notifications_cache', 'resave_description', 'send_email', 'push', '']
    date_hierarchy = 'created'
    list_select_related = ('recipient', 'actor')
    list_display = ('id', '__str__', 'recipient', 'actor', 'is_read', 'created')
    list_filter = ('is_read', OldListFilter, 'event')
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

        self.clear_unread_notifications_cache(request, queryset)
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

        self.clear_unread_notifications_cache(request, queryset)
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
        if 'email' not in whistle_settings.CHANNELS:
            messages.error(request, _('E-mail channel is disabled'))
            return

        for notification in queryset:
            notification.send_mail()
    send_email.short_description = _('Send email')

    def resave_description(self, request, queryset):
        for notification in queryset:
            print(notification.resave_description())
    resave_description.short_description = _('Resave description')

    def push(self, request, queryset):
        if 'push' not in whistle_settings.CHANNELS:
            messages.error(request, _('Push channel is disabled'))
            return

        for notification in queryset:
            notification.push()
    push.short_description = _('Push')
