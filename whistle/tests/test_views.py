import pytest
from django.core import signing
from django.urls import reverse

from whistle import settings as whistle_settings
from whistle.models import Notification


@pytest.mark.django_db
class TestNotificationListView:
    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        response = client.get(reverse('notifications:list'))
        # Should redirect to login
        assert response.status_code == 302

    def test_list_view_authenticated(self, client_logged_in, user, other_user):
        """Test list view shows user's notifications."""
        # Create notifications
        Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        response = client_logged_in.get(reverse('notifications:list'))
        assert response.status_code == 200

    def test_list_view_marks_as_read(self, client_logged_in, user, other_user):
        """Test list view marks notifications as read."""
        notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        response = client_logged_in.get(reverse('notifications:list'))

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_list_view_pagination(self, client_logged_in, user, other_user):
        """Test list view pagination."""
        # Create more than paginate_by notifications
        for i in range(15):
            Notification.objects.create(
                recipient=user,
                event='TEST_EVENT',
                actor=other_user
            )

        response = client_logged_in.get(reverse('notifications:list'))
        assert response.status_code == 200
        # Check pagination context
        assert 'page_obj' in response.context

    def test_list_view_only_user_notifications(
        self, client_logged_in, user, other_user
    ):
        """Test list view only shows logged in user's notifications."""
        # Create notification for other user
        Notification.objects.create(
            recipient=other_user,
            event='TEST_EVENT',
            actor=user
        )
        # Create notification for logged in user
        user_notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        response = client_logged_in.get(reverse('notifications:list'))

        queryset = response.context['object_list']
        assert queryset.count() == 1
        assert queryset.first() == user_notification


@pytest.mark.django_db
class TestReadNotificationByHashView:
    def test_read_by_hash_success(self, client, user, other_user):
        """Test reading notification by hash succeeds."""
        notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        hash_value = notification.hash
        response = client.get(
            reverse('notifications:read_notification', kwargs={'hash': hash_value})
        )

        assert response.status_code == 200
        assert response.content == b'OK'

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_read_by_hash_already_read(self, client, user, other_user):
        """Test reading already read notification."""
        notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=True
        )

        hash_value = notification.hash
        response = client.get(
            reverse('notifications:read_notification', kwargs={'hash': hash_value})
        )

        assert response.status_code == 200
        assert response.content == b'ALREADY READ'

    def test_read_by_hash_bad_signature(self, client):
        """Test reading with bad signature."""
        response = client.get(
            reverse('notifications:read_notification', kwargs={'hash': 'invalid-hash'})
        )

        assert response.status_code == 200
        assert response.content == b'BAD SIGNATURE'

    def test_read_by_hash_not_found(self, client, user):
        """Test reading non-existent notification."""
        # Create a valid hash but for non-existent notification
        protect = {'notification_id': 99999, 'recipient_id': user.pk}
        hash_value = signing.dumps(
            protect,
            key=whistle_settings.SIGNING_KEY,
            salt=whistle_settings.SIGNING_SALT
        )

        response = client.get(
            reverse('notifications:read_notification', kwargs={'hash': hash_value})
        )

        assert response.status_code == 200
        assert response.content == b'NOT FOUND'

    def test_read_by_hash_invalid_recipient(self, client, user, other_user):
        """Test reading notification with wrong recipient in hash."""
        notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        # Create hash with wrong recipient
        protect = {'notification_id': notification.pk, 'recipient_id': other_user.pk}
        hash_value = signing.dumps(
            protect,
            key=whistle_settings.SIGNING_KEY,
            salt=whistle_settings.SIGNING_SALT
        )

        response = client.get(
            reverse('notifications:read_notification', kwargs={'hash': hash_value})
        )

        assert response.status_code == 200
        assert response.content == b'INVALID RECIPIENT'

        notification.refresh_from_db()
        assert notification.is_read is False


@pytest.mark.django_db
class TestNotificationSettingsView:
    def test_settings_view_requires_login(self, client):
        """Test settings view requires authentication."""
        response = client.get(reverse('notifications:settings'))
        assert response.status_code == 302

    def test_settings_view_get(self, client_logged_in):
        """Test settings view GET request."""
        response = client_logged_in.get(reverse('notifications:settings'))
        assert response.status_code == 200

    def test_settings_view_post(self, client_logged_in, user):
        """Test settings view POST request."""
        response = client_logged_in.post(
            reverse('notifications:settings'),
            data={
                'web': True,
                'email': False,
            }
        )

        # Should redirect on success
        assert response.status_code == 302

        user.refresh_from_db()
        assert user.notification_settings is not None
