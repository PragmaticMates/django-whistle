from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whistle', '0006_auto_20221116_1525'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read'], name='whistle_recipient_is_read'),
        ),
    ]
