import pytest
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from whistle.models import Notification
from whistle.managers import NotificationManager, NotificationQuerySet


@pytest.mark.django_db
class TestNotificationQuerySet:
    def test_unread_filter(self, user, other_user):
        """Test filtering unread notifications."""
        Notification.objects.create(
            recipient=user, event='TEST_EVENT', actor=other_user, is_read=False
        )
        Notification.objects.create(
            recipient=user, event='TEST_EVENT', actor=other_user, is_read=True
        )

        unread = Notification.objects.unread()
        assert unread.count() == 1
        assert unread.first().is_read is False

    def test_mark_as_read(self, multiple_notifications):
        """Test marking notifications as read."""
        unread_count = Notification.objects.unread().count()
        assert unread_count > 0

        Notification.objects.unread().mark_as_read()

        assert Notification.objects.unread().count() == 0

    def test_for_recipient_authenticated(self, user, other_user):
        """Test filtering by authenticated recipient."""
        Notification.objects.create(
            recipient=user, event='TEST_EVENT', actor=other_user
        )
        Notification.objects.create(
            recipient=other_user, event='TEST_EVENT', actor=user
        )

        user_notifications = Notification.objects.for_recipient(user)
        assert user_notifications.count() == 1
        assert user_notifications.first().recipient == user

    def test_for_recipient_unauthenticated(self, user, other_user):
        """Test filtering returns none for unauthenticated user."""
        Notification.objects.create(
            recipient=user, event='TEST_EVENT', actor=other_user
        )

        # Create a mock unauthenticated user
        anon_user = Mock()
        anon_user.is_authenticated = False

        anon_notifications = Notification.objects.for_recipient(anon_user)
        assert anon_notifications.count() == 0

    def test_of_object(self, user, other_user):
        """Test filtering by object."""
        content_type = ContentType.objects.get_for_model(user)
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            object_content_type=content_type,
            object_id=user.pk
        )
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        object_notifications = Notification.objects.of_object(user)
        assert object_notifications.count() == 1

    def test_of_target(self, user, other_user):
        """Test filtering by target."""
        content_type = ContentType.objects.get_for_model(other_user)
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            target_content_type=content_type,
            target_id=other_user.pk
        )

        target_notifications = Notification.objects.of_target(other_user)
        assert target_notifications.count() == 1

    def test_of_object_or_target(self, user, other_user):
        """Test filtering by object or target."""
        content_type = ContentType.objects.get_for_model(user)

        # Notification with user as object
        Notification.objects.create(
            recipient=other_user,
            event='TEST_EVENT',
            actor=other_user,
            object_content_type=content_type,
            object_id=user.pk
        )
        # Notification with user as target
        Notification.objects.create(
            recipient=other_user,
            event='TEST_EVENT',
            actor=other_user,
            target_content_type=content_type,
            target_id=user.pk
        )
        # Unrelated notification
        Notification.objects.create(
            recipient=other_user,
            event='TEST_EVENT',
            actor=other_user
        )

        related_notifications = Notification.objects.of_object_or_target(user)
        assert related_notifications.count() == 2

    def test_old_with_threshold(self, user, other_user):
        """Test filtering old notifications."""
        # Create an old notification
        old_notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )
        # Manually set created to be old
        Notification.objects.filter(pk=old_notification.pk).update(
            created=now() - timedelta(days=60)
        )

        # Create a recent notification
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        old_notifications = Notification.objects.old(threshold=timedelta(days=30))
        assert old_notifications.count() == 1

    def test_old_without_threshold(self, user, other_user):
        """Test old() returns none when threshold is None."""
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        old_notifications = Notification.objects.old(threshold=None)
        assert old_notifications.count() == 0

    def test_not_old_with_threshold(self, user, other_user):
        """Test filtering recent notifications."""
        # Create an old notification
        old_notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )
        Notification.objects.filter(pk=old_notification.pk).update(
            created=now() - timedelta(days=60)
        )

        # Create a recent notification
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        recent_notifications = Notification.objects.not_old(threshold=timedelta(days=30))
        assert recent_notifications.count() == 1

    def test_not_old_without_threshold(self, user, other_user):
        """Test not_old() returns all when threshold is None."""
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        recent_notifications = Notification.objects.not_old(threshold=None)
        assert recent_notifications.count() == 1


@pytest.mark.django_db
class TestNotificationManager:
    def test_is_channel_available(self, user):
        """Test channel availability check."""
        manager = NotificationManager()

        # web and email are in default channels
        assert manager.is_channel_available(user, 'web') is True
        assert manager.is_channel_available(user, 'email') is True
        assert manager.is_channel_available(user, 'push') is False

    def test_is_notification_available_default(self, user):
        """Test notification availability with default settings."""
        manager = NotificationManager()

        assert manager.is_notification_available(user, 'web', 'TEST_EVENT') is True
        assert manager.is_notification_available(user, 'email', 'TEST_EVENT') is True

    def test_is_notification_enabled_default(self, user):
        """Test notification enabled check with default settings."""
        manager = NotificationManager()

        # With no user settings, should be enabled by default
        assert manager.is_notification_enabled(user, 'web', 'TEST_EVENT') is True
        assert manager.is_notification_enabled(user, 'email', 'TEST_EVENT') is True

    def test_is_notification_enabled_user_settings(self, user):
        """Test notification enabled with user settings."""
        user.notification_settings = {
            'channels': {'web': True, 'email': False},
            'events': {}
        }
        user.save()

        manager = NotificationManager()

        assert manager.is_notification_enabled(user, 'web', 'TEST_EVENT') is True
        assert manager.is_notification_enabled(user, 'email', 'TEST_EVENT') is False

    def test_is_notification_enabled_event_settings(self, user):
        """Test notification enabled with event-specific settings."""
        user.notification_settings = {
            'channels': {'web': True, 'email': True},
            'events': {
                'web': {'test_event': False},
                'email': {'test_event': True}
            }
        }
        user.save()

        manager = NotificationManager()

        assert manager.is_notification_enabled(user, 'web', 'TEST_EVENT') is False
        assert manager.is_notification_enabled(user, 'email', 'TEST_EVENT') is True

    def test_is_channel_enabled(self, user):
        """Test is_channel_enabled method."""
        user.notification_settings = {
            'channels': {'web': True, 'email': False}
        }
        user.save()

        manager = NotificationManager()

        assert manager.is_channel_enabled(user, 'web') is True
        assert manager.is_channel_enabled(user, 'email') is False

    def test_notify_creates_web_notification(self, user, other_user):
        """Test notify creates web notification."""
        manager = NotificationManager()

        initial_count = Notification.objects.count()
        manager.notify(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        assert Notification.objects.count() == initial_count + 1

    def test_notify_inactive_user(self, inactive_user, other_user):
        """Test notify does nothing for inactive user."""
        manager = NotificationManager()

        initial_count = Notification.objects.count()
        manager.notify(
            recipient=inactive_user,
            event='TEST_EVENT',
            actor=other_user
        )

        assert Notification.objects.count() == initial_count

    def test_notify_disabled_channel(self, user, other_user):
        """Test notify respects disabled channels."""
        user.notification_settings = {
            'channels': {'web': False, 'email': False}
        }
        user.save()

        manager = NotificationManager()

        initial_count = Notification.objects.count()
        manager.notify(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        # No web notification should be created
        assert Notification.objects.count() == initial_count

    def test_get_event_context(self, user, other_user):
        """Test get_event_context returns proper context."""
        manager = NotificationManager()

        context = manager.get_event_context(
            event='TEST_EVENT',
            actor=other_user,
            object=user,
            target=None
        )

        assert context['actor'] == other_user
        assert context['object'] == user
        assert context['target'] == ''
        assert 'testuser' in context  # model name lowercase

    def test_get_description(self, user, other_user):
        """Test get_description renders template correctly."""
        manager = NotificationManager()

        description = manager.get_description(
            event='TEST_EVENT',
            actor=other_user,
            object=user,
            target=None,
            pass_variables=True
        )

        assert other_user.username in description
        assert 'performed action' in description

    def test_get_description_without_variables(self, user, other_user):
        """Test get_description without variables."""
        manager = NotificationManager()

        description = manager.get_description(
            event='TEST_EVENT',
            actor=other_user,
            object=user,
            target=None,
            pass_variables=False
        )

        # Variables should be stripped
        assert other_user.username not in description

    def test_get_push_config(self, notification):
        """Test get_push_config returns proper config."""
        manager = NotificationManager()

        config = manager.get_push_config(notification)

        assert 'title' in config
        assert 'body' in config
        assert 'android' in config
        assert 'apns' in config
        assert config['android']['priority'] == 'high'
