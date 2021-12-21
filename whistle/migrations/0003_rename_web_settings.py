from django.core.management import call_command
from django.db import migrations


def notification_to_web(apps, schema_editor):
    try:
        call_command('copy_channel_settings', 'notification', 'web', delete=True)
    except:
        pass


def web_to_notification(apps, schema_editor):
    try:
        call_command('copy_channel_settings', 'web', 'notification', delete=True)
    except:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('whistle', '0002_notification_details'),
    ]

    operations = [
        migrations.RunPython(notification_to_web, web_to_notification),
    ]
