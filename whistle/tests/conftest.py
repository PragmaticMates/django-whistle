import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from whistle.models import Notification


@pytest.fixture
def user(db):
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def inactive_user(db):
    """Create an inactive test user."""
    User = get_user_model()
    return User.objects.create_user(
        username='inactiveuser',
        email='inactive@example.com',
        password='testpass123',
        is_active=False
    )


@pytest.fixture
def other_user(db):
    """Create another test user."""
    User = get_user_model()
    return User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpass123'
    )


@pytest.fixture
def notification(db, user, other_user):
    """Create a test notification."""
    return Notification.objects.create(
        recipient=user,
        event='TEST_EVENT',
        actor=other_user,
        object_content_type=ContentType.objects.get_for_model(user),
        object_id=user.pk,
        details='Test notification details'
    )


@pytest.fixture
def unread_notification(db, user, other_user):
    """Create an unread notification."""
    return Notification.objects.create(
        recipient=user,
        event='TEST_EVENT',
        actor=other_user,
        is_read=False
    )


@pytest.fixture
def read_notification(db, user, other_user):
    """Create a read notification."""
    return Notification.objects.create(
        recipient=user,
        event='TEST_EVENT',
        actor=other_user,
        is_read=True
    )


@pytest.fixture
def multiple_notifications(db, user, other_user):
    """Create multiple notifications for testing."""
    notifications = []
    for i in range(5):
        n = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=(i % 2 == 0)  # Alternate read/unread
        )
        notifications.append(n)
    return notifications


@pytest.fixture
def client_logged_in(client, user):
    """Return a client with logged in user."""
    client.force_login(user)
    return client
