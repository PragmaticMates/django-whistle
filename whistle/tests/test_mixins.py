import pytest
from django.core.cache import cache

from whistle.models import Notification
from whistle.mixins import UserNotificationsMixin


@pytest.mark.django_db
class TestUserNotificationsMixin:
    def test_unread_notifications_count_no_notifications(self, user):
        """Test unread count with no notifications."""
        cache.clear()
        count = user.unread_notifications_count
        assert count == 0

    def test_unread_notifications_count_with_notifications(self, user, other_user):
        """Test unread count with notifications."""
        cache.clear()

        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=True
        )

        count = user.unread_notifications_count
        assert count == 2

    def test_unread_notifications_property(self, user, other_user):
        """Test unread notifications property."""
        cache.clear()

        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        unread = user.unread_notifications
        assert len(unread) == 1

    def test_unread_notifications_caching(self, user, other_user):
        """Test that unread notifications are cached."""
        cache.clear()

        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        # First call should populate cache
        unread1 = user.unread_notifications
        assert len(unread1) == 1

        # Create another notification
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        # Second call should return cached value
        unread2 = user.unread_notifications
        # Cached value still has 1
        assert len(unread2) == 1

    def test_clear_unread_notifications_cache(self, user, other_user):
        """Test clearing unread notifications cache."""
        cache.clear()

        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        # Populate cache
        _ = user.unread_notifications

        # Create another notification
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        # Clear cache
        user.clear_unread_notifications_cache()

        # Should now show 2
        unread = user.unread_notifications
        assert len(unread) == 2

    def test_notification_settings_default(self, user):
        """Test notification_settings default value."""
        assert user.notification_settings is None

    def test_notification_settings_json(self, user):
        """Test notification_settings JSON storage."""
        user.notification_settings = {
            'channels': {'web': True, 'email': False},
            'events': {'web': {'test_event': True}}
        }
        user.save()

        user.refresh_from_db()
        assert user.notification_settings['channels']['web'] is True
        assert user.notification_settings['channels']['email'] is False

    def test_unread_notifications_count_cached(self, user, other_user):
        """Test unread count uses cached notifications."""
        cache.clear()

        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        # First get unread_notifications to populate cache
        _ = user.unread_notifications

        # Now get count - should use cache
        count = user.unread_notifications_count
        assert count == 1

    def test_unread_notifications_object_display(self, user, other_user):
        """Test unread notifications have object_display attribute."""
        from django.contrib.contenttypes.models import ContentType
        cache.clear()

        ct = ContentType.objects.get_for_model(user)
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            object_content_type=ct,
            object_id=user.pk,
            is_read=False
        )

        unread = user.unread_notifications
        notification = unread[0]

        assert hasattr(notification, 'object_display')
        assert notification.object_display == str(user)

    def test_cache_key_constant(self):
        """Test cache key is defined correctly."""
        assert UserNotificationsMixin.CACHE_KEY == 'user_unread_notifications'
