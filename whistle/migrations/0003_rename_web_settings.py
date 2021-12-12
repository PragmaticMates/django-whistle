from django.contrib.auth import get_user_model
from django.db import migrations


def rename_channel(old, new):
    user_model = get_user_model()

    settings_field = None
    settings_possible_fields = ['notification_settings', 'notices_settings']

    for possible_field in settings_possible_fields:
        if hasattr(user_model, possible_field):
            settings_field = possible_field

    if settings_field is not None:
        for user in user_model.objects.exclude(**{settings_field: None}):
            notification_settings = getattr(user, settings_field)

            try:
                notification_settings[new] = notification_settings.pop(old)
                user.save(update_fields=[settings_field])
            except KeyError:
                pass

            # print(user, user.notification_settings)


def notification_to_web(apps, schema_editor):
    rename_channel('notification', 'web')


def web_to_notification(apps, schema_editor):
    rename_channel('web', 'notification')


class Migration(migrations.Migration):

    dependencies = [
        ('whistle', '0002_notification_details'),
    ]

    operations = [
        migrations.RunPython(notification_to_web, web_to_notification),
    ]
