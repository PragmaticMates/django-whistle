from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import migrations


def mail_to_email(apps, schema_editor):
    try:
        call_command('copy_channel_settings', 'mail', 'email', delete=True)
    except:
        pass


def email_to_mail(apps, schema_editor):
    try:
        call_command('copy_channel_settings', 'email', 'mail', delete=True)
    except:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('whistle', '0003_rename_web_settings'),
    ]

    operations = [
        migrations.RunPython(mail_to_email, email_to_mail),
    ]
