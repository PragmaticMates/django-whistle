from django.contrib.auth import get_user_model
from django.db import migrations


def wrap(apps, schema_editor):
    for user in get_user_model().objects.exclude(notification_settings=None):
        user.notification_settings = {
            'events': user.notification_settings
        }
        user.save(update_fields=['notification_settings'])


def unwrap(apps, schema_editor):
    for user in get_user_model().objects.exclude(notification_settings=None):
        user.notification_settings = user.notification_settings.get('events', {})
        user.save(update_fields=['notification_settings'])


class Migration(migrations.Migration):

    dependencies = [
        ('whistle', '0004_rename_mail_to_email'),
    ]

    operations = [
        migrations.RunPython(wrap, unwrap),
    ]
