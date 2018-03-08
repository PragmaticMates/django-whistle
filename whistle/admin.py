from django.contrib import admin
from django.utils.translation import ugettext_lazy as _, ngettext
from whistle.forms import NotificationAdminForm
from whistle.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    actions = ['make_unread', 'make_read']
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
