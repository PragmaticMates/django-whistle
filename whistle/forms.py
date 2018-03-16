from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, HTML, Field, Layout, Submit
from django import forms
from django.utils.translation import ugettext_lazy as _

from whistle.managers import NoticeManager
from whistle.models import Notification
from whistle import settings as whistle_settings


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


class EditNoticesForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(EditNoticesForm, self).__init__(*args, **kwargs)
        self.user = user
        self.init_fields()
        self.init_form_helper()

    @property
    def labels(self):
        return dict(whistle_settings.EVENTS)

    def get_initial_value(self, channel, event):
        return NoticeManager.is_notice_allowed(self.user, channel, event)

    def init_fields(self):
        for event, label in self.labels.items():
            event_identifier = event.lower()
            mail_field_name = 'mail_{}'.format(event_identifier)
            notification_field_name = 'notification_{}'.format(event_identifier)

            self.fields.update({
                mail_field_name: forms.BooleanField(label=_('Mail'), required=False, initial=self.get_initial_value('mail', event)),
                notification_field_name: forms.BooleanField(label=_('Notification'), required=False, initial=self.get_initial_value('notification', event)),
            })

    def init_form_helper(self):
        fields = []

        for event, label in self.labels.items():
            event_identifier = event.lower()
            mail_field_name = 'mail_{}'.format(event_identifier)
            notification_field_name = 'notification_{}'.format(event_identifier)

            field = Div(
                Div(HTML('<p>{}</p>'.format(label)), css_class='col-md-6'),
                Div(Field(notification_field_name, css_class='switch'), css_class='col-md-3'),
                Div(Field(mail_field_name, css_class='switch'), css_class='col-md-3'),
                css_class='row'
            )

            fields.append(field)

        fields.append(
            FormActions(
                Submit('submit', _('Save'), css_class='btn-lg')
            )
        )

        self.helper = FormHelper()
        self.helper.form_class = 'notices-settings'
        self.helper.layout = Layout(*fields)

    def clean(self):
        settings = {'mail': {}, 'notification': {}}

        for event in self.labels.keys():
            event_identifier = event.lower()
            mail_field_name = 'mail_{}'.format(event_identifier)
            notification_field_name = 'notification_{}'.format(event_identifier)

            settings['mail'][event_identifier] = self.cleaned_data.get(mail_field_name, False)
            settings['notification'][event_identifier] = self.cleaned_data.get(notification_field_name, False)

        return settings
