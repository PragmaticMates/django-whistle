from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Copies notification settings from one channel to another. ' \
           'Suitable for altering a lot of event types.'

    def add_arguments(self, parser):
        parser.add_argument('from-channel', nargs=1, type=str)
        parser.add_argument('to-channel', nargs=1, type=str)
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete origin channel settings',
        )

    def handle(self, *args, **options):
        from_channel = options['from-channel'][0]
        to_channel = options['to-channel'][0]
        self.copy(from_channel, to_channel, options['delete'])

    def copy(self, from_channel, to_channel, delete):
        print(f"{'Moving' if delete else 'Copying'} from channel {from_channel} to {to_channel}")

        user_model = get_user_model()

        settings_field = None
        settings_possible_fields = ['notification_settings', 'notices_settings']

        for possible_field in settings_possible_fields:
            if hasattr(user_model, possible_field):
                settings_field = possible_field

        print(f'Notification settings field = {settings_field}')

        if settings_field is not None:
            for user in user_model.objects.exclude(**{settings_field: None}):
                notification_settings = getattr(user, settings_field)

                # TODO: channels and events

                if from_channel in notification_settings:
                    if delete:
                        notification_settings[to_channel] = notification_settings.pop(from_channel)
                    else:
                        notification_settings[to_channel] = notification_settings[from_channel]

                    setattr(user, settings_field, notification_settings)  # Python 3.9.5 bug
                    user.save(update_fields=[settings_field])
                else:
                    print(f'Channel {from_channel} not in notification settings of user {user}')

