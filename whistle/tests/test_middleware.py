import pytest
from unittest.mock import Mock, MagicMock, patch

from django.http import HttpResponse
from django.views.generic import DetailView

from whistle import settings as whistle_settings
from whistle.middleware import ReadNotificationMiddleware
from whistle.models import Notification


@pytest.mark.django_db
class TestReadNotificationMiddleware:
    def test_middleware_init(self):
        """Test middleware initialization."""
        get_response = Mock()
        middleware = ReadNotificationMiddleware(get_response)
        assert middleware.get_response == get_response

    def test_middleware_marks_notification_read_via_url_param(
        self, user, other_user, client
    ):
        """Test middleware marks notification as read via URL param."""
        notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=False
        )

        client.force_login(user)
        response = client.get(
            f'/notifications/?{whistle_settings.URL_PARAM}={notification.pk}'
        )

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_middleware_ignores_other_user_notification(
        self, user, other_user, client
    ):
        """Test middleware doesn't mark other user's notification as read."""
        notification = Notification.objects.create(
            recipient=other_user,
            event='TEST_EVENT',
            actor=user,
            is_read=False
        )

        client.force_login(user)
        response = client.get(
            f'/notifications/?{whistle_settings.URL_PARAM}={notification.pk}'
        )

        notification.refresh_from_db()
        assert notification.is_read is False

    def test_middleware_ignores_already_read_notification(
        self, user, other_user, client
    ):
        """Test middleware handles already read notification."""
        notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            is_read=True
        )

        client.force_login(user)
        # Should not raise an error
        response = client.get(
            f'/notifications/?{whistle_settings.URL_PARAM}={notification.pk}'
        )

        assert response.status_code == 200

    def test_middleware_handles_invalid_notification_id(self, user, client):
        """Test middleware handles invalid notification ID gracefully."""
        client.force_login(user)
        # Should not raise an error
        response = client.get(
            f'/notifications/?{whistle_settings.URL_PARAM}=99999'
        )

        assert response.status_code == 200

    def test_middleware_unauthenticated_user(self, client):
        """Test middleware does nothing for unauthenticated user."""
        response = client.get(
            f'/notifications/?{whistle_settings.URL_PARAM}=1'
        )
        # Redirects to login or returns 302/403
        assert response.status_code in [200, 302, 403]

    def test_middleware_without_url_param(self, user, client):
        """Test middleware processes request without URL param."""
        client.force_login(user)
        response = client.get('/notifications/')

        assert response.status_code == 200

    def test_middleware_detail_view_marks_notifications_read(
        self, user, other_user
    ):
        """Test middleware marks notifications read on DetailView."""
        from django.contrib.contenttypes.models import ContentType

        # Create notification with object
        ct = ContentType.objects.get_for_model(user)
        notification = Notification.objects.create(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            object_content_type=ct,
            object_id=user.pk,
            is_read=False
        )

        # Mock the get_response to return a response with context_data
        def get_response(request):
            response = HttpResponse()
            response.context_data = {
                'view': Mock(spec=DetailView),
                'object': user
            }
            return response

        middleware = ReadNotificationMiddleware(get_response)

        # Create mock request with user object
        request = Mock()
        request.user = user
        request.GET = {}

        response = middleware(request)

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_middleware_handles_response_without_context(self, user):
        """Test middleware handles response without context_data."""
        def get_response(request):
            return HttpResponse('No context')

        middleware = ReadNotificationMiddleware(get_response)

        request = Mock()
        request.user = user
        request.GET = {}

        # Should not raise an error
        response = middleware(request)
        assert response is not None
