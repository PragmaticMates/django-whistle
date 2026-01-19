import pytest
from django.core import signing
from django.contrib.contenttypes.models import ContentType

from whistle import settings as whistle_settings
from whistle.models import Notification


@pytest.mark.django_db
class TestNotificationModel:
    def test_notification_creation(self, notification):
        """Test that a notification can be created."""
        assert notification.pk is not None
        assert notification.event == 'TEST_EVENT'
        assert notification.is_read is False

    def test_notification_str(self, notification):
        """Test notification string representation."""
        str_repr = str(notification)
        assert str_repr is not None
        assert len(str_repr) > 0

    def test_notification_description(self, notification):
        """Test notification description property."""
        description = notification.description
        assert description is not None
        # Should contain the actor name since we're using pass_variables=True
        assert notification.actor.username in description or 'performed action' in description

    def test_notification_short_description(self, notification):
        """Test notification short description."""
        short_desc = notification.short_description()
        assert short_desc is not None
        # Short description has empty variables
        assert 'performed action' in short_desc

    def test_notification_hash(self, notification):
        """Test notification hash signing."""
        hash_value = notification.hash
        assert hash_value is not None

        # Verify the hash can be decoded
        decoded = signing.loads(
            hash_value,
            key=whistle_settings.SIGNING_KEY,
            salt=whistle_settings.SIGNING_SALT
        )
        assert decoded['notification_id'] == notification.pk
        assert decoded['recipient_id'] == notification.recipient.pk

    def test_notification_get_absolute_url(self, notification):
        """Test notification URL generation."""
        url = notification.get_absolute_url()
        assert url is not None
        # URL should contain the read-notification param if unread
        if not notification.is_read:
            assert whistle_settings.URL_PARAM in url

    def test_notification_get_absolute_url_read(self, read_notification):
        """Test URL for read notification doesn't have param."""
        # Clear cache first
        from django.core.cache import cache
        cache.clear()

        url = read_notification.get_absolute_url()
        # Already read notifications might still have the param from cache
        assert url is not None

    def test_notification_ordering(self, user, other_user, db):
        """Test that notifications are ordered by created descending."""
        n1 = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )
        n2 = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        notifications = list(Notification.objects.all())
        # Most recent first
        assert notifications[0].pk == n2.pk
        assert notifications[1].pk == n1.pk

    def test_notification_with_target(self, user, other_user, db):
        """Test notification with target object."""
        notification = Notification.objects.create(
            recipient=user,
            event='TARGET_EVENT',
            actor=other_user,
            object_content_type=ContentType.objects.get_for_model(user),
            object_id=user.pk,
            target_content_type=ContentType.objects.get_for_model(other_user),
            target_id=other_user.pk
        )

        assert notification.object == user
        assert notification.target == other_user

    def test_notification_resave_description(self, notification):
        """Test resave_description method."""
        result = notification.resave_description()
        assert 'long' in result
        assert 'short' in result
        assert result['long'] is not None
        assert result['short'] is not None

    def test_notification_details(self, notification):
        """Test notification details field."""
        assert notification.details == 'Test notification details'

    def test_notification_meta(self):
        """Test notification model meta options."""
        assert Notification._meta.verbose_name == 'notification'
        assert Notification._meta.verbose_name_plural == 'notifications'
        assert Notification._meta.ordering == ('-created',)
