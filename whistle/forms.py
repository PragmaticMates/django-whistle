import re

from django import forms
from django.utils.translation import gettext, gettext_lazy as _
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, HTML, Field, Layout, Submit

from whistle import settings as whistle_settings
from whistle.helpers import strip_unwanted_chars
from whistle.models import Notification
from whistle.settings import notification_manager


class NotificationAdminForm(forms.ModelForm):
    class Meta:
        model = Notification
        exclude = ()

    def clean(self):
        event = self.cleaned_data.get('event', None)

        if event is not None:
            event_display = dict(whistle_settings.EVENTS).get(event)
            error = _('This field is required for selected event.')

            ctx_mapping = {
                'object_id': 'object',
                'target_id': 'target',
                'actor': 'actor',
            }

            for field, variable in ctx_mapping.items():
                value = self.cleaned_data.get(field, None)
                if value is None and '%({})s'.format(variable) in event_display:
                    self.add_error(field, error)

        return self.cleaned_data


class NotificationSettingsForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(NotificationSettingsForm, self).__init__(*args, **kwargs)
        self.user = user
        self.init_fields()
        self.init_form_helper()

    @property
    def labels(self):
        events = dict(whistle_settings.EVENTS)

        for event, label in events.items():
            new_label = strip_unwanted_chars(label)
            events[event] = new_label

        return events

    def channel_labels(self, channel):
        return {
            'web': _('Web'),
            'email': _('E-mail'),
            'push': _('Push')
        }.get(channel, channel)

    def field_names(self, event):
        event_identifier = event.lower()

        return {
            'web': 'web_{}'.format(event_identifier),
            'email': 'email_{}'.format(event_identifier),
            'push': 'push_{}'.format(event_identifier)
        }

    def get_initial_value(self, channel, event=None):
        return notification_manager.is_notification_enabled(self.user, channel, event, bypass_channel=True)

    def init_fields(self):
        for channel in whistle_settings.CHANNELS:
            if notification_manager.is_channel_available(self.user, channel):
                self.fields.update({
                    channel: forms.BooleanField(
                        label=self.channel_labels(channel),
                        required=False,
                        initial=self.get_initial_value(channel)),
                })

        for event, label in self.labels.items():
            field_names = self.field_names(event)

            for channel in whistle_settings.CHANNELS:
                if notification_manager.is_notification_available(self.user, channel, event):
                    self.fields.update({
                        field_names[channel]: forms.BooleanField(
                            label=self.channel_labels(channel),
                            required=False,
                            initial=self.get_initial_value(channel, event)),
                    })

    def init_form_helper(self):
        fields = []
        channel_fields = []

        for channel in whistle_settings.CHANNELS:
            if notification_manager.is_channel_available(self.user, channel):
                channel_fields.append(
                    Div(Field(channel, css_class='switch'), css_class='channel fw-bold col-md mb-3')
                )

        fields.append(Div(
                Div(HTML('<p>{}</p>'.format(_(''))), css_class='col-md-6'),
                *channel_fields,
                css_class='row'
            )
        )

        for event, label in self.labels.items():
            field_names = self.field_names(event)
            event_fields = []

            for channel in whistle_settings.CHANNELS:
                if notification_manager.is_notification_available(self.user, channel, event):
                    event_fields.append(
                        Div(Field(field_names[channel], css_class='switch'), css_class='col-md')
                    )

            if len(event_fields) > 0:
                fields.append(Div(
                        Div(HTML('<p>{}</p>'.format(label)), css_class='col-md-6'),
                        *event_fields,
                        css_class='row'
                    )
                )

        fields.append(
            FormActions(
                Submit('submit', _('Save'), css_class='btn-lg')
            )
        )

        self.helper = FormHelper()
        self.helper.form_class = 'notification-settings'
        self.helper.layout = Layout(*fields)

    def clean(self):
        settings = {'channels': {}, 'events': {}}

        for channel in whistle_settings.CHANNELS:
            if notification_manager.is_channel_available(self.user, channel):
                settings['channels'][channel] = self.cleaned_data.get(channel)

        # events
        for event in self.labels.keys():
            field_names = self.field_names(event)
            event_identifier = event.lower()

            for channel in whistle_settings.CHANNELS:
                if notification_manager.is_channel_available(self.user, channel) and \
                        notification_manager.is_notification_available(self.user, channel, event):
                    if channel not in settings['events']:
                        settings['events'][channel] = {}

                    settings['events'][channel][event_identifier] = self.cleaned_data.get(field_names[channel])

        return settings
