import re

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, HTML, Field, Layout, Submit
from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext

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
        events = dict(whistle_settings.EVENTS)

        for event, label in events.items():
            pat = re.compile(r'%\(.*\)s|"%\(.*\)s"')
            new_label = re.sub(pat, '', ugettext(label))  # remove all variable placeholders
            new_label = new_label.replace("''", '')  # remove all 2 single quotas
            new_label = new_label.replace('""', '')  # remove all 2 double quotas
            new_label = new_label.strip(' :.')  # remove trailing spaces and semicolons
            new_label = re.sub(' +', ' ', new_label)  # remove all multiple spaces

            events[event] = new_label

        return events

    def get_initial_value(self, channel, event):
        return NoticeManager.is_notice_allowed(self.user, channel, event)

    def init_fields(self):
        for event, label in self.labels.items():
            event_identifier = event.lower()
            field_names = {
                'web': 'notification_{}'.format(event_identifier),  # TODO: migrate 'notification' to 'web'
                'mail': 'mail_{}'.format(event_identifier),
                'push': 'push_{}'.format(event_identifier)
            }

            self.fields.update({
                field_names['web']: forms.BooleanField(label=_('Web'), required=False, initial=self.get_initial_value('notification', event)),  # TODO: migrate 'notification' to 'web'
                field_names['mail']: forms.BooleanField(label=_('Mail'), required=False, initial=self.get_initial_value('mail', event)),
                field_names['push']: forms.BooleanField(label=_('Push'), required=False, initial=self.get_initial_value('push', event))
            })

    def init_form_helper(self):
        fields = []

        for event, label in self.labels.items():
            event_identifier = event.lower()

            field_names = {
                'web': 'notification_{}'.format(event_identifier),  # TODO: migrate 'notification' to 'web'
                'mail': 'mail_{}'.format(event_identifier),
                'push': 'push_{}'.format(event_identifier)
            }

            field = Div(
                Div(HTML('<p>{}</p>'.format(label)), css_class='col-md-6'),
                Div(Field(field_names['web'], css_class='switch'), css_class='col-md'),
                Div(Field(field_names['mail'], css_class='switch'), css_class='col-md'),
                Div(Field(field_names['push'], css_class='switch'), css_class='col-md'),
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
        settings = {'mail': {}, 'notification': {}, 'push': {}}  # TODO: migrate 'notification' to 'web'

        for event in self.labels.keys():
            event_identifier = event.lower()

            field_names = {
                'web': 'notification_{}'.format(event_identifier),  # TODO: migrate 'notification' to 'web'
                'mail': 'mail_{}'.format(event_identifier),
                'push': 'push_{}'.format(event_identifier)
            }

            settings['notification'][event_identifier] = self.cleaned_data.get(field_names['web'], False)  # TODO: migrate 'notification' to 'web'
            settings['mail'][event_identifier] = self.cleaned_data.get(field_names['mail'], False)
            settings['push'][event_identifier] = self.cleaned_data.get(field_names['push'], False)

        return settings
