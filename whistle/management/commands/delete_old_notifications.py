from django.core.management import BaseCommand

from whistle.models import Notification
from whistle import settings as whistle_settings


class Command(BaseCommand):
    help = 'Deletes old notifications based by threshold settings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Don't delete notifications, just outputs the number of old notifications.",
        )

    def handle(self, *args, **options):
        threshold = whistle_settings.OLD_THRESHOLD
        print(f'Old threshold (age): {threshold}')

        if threshold is None:
            exit('Threshold is not set. Not deleting any notifications.')

        old_notifications = Notification.objects.old()
        print(f'Number of old notifications: {old_notifications.count()}')

        if options['dry_run']:
            exit('Dry run. Not deleting any notifications.')

        old_notifications.delete()
        print('Old notifications deleted.')
