from django.contrib.auth.models import AbstractUser

from whistle.mixins import UserNotificationsMixin


class TestUser(UserNotificationsMixin, AbstractUser):
    """Custom user model for testing that includes notification mixin."""

    class Meta:
        app_label = 'tests'
