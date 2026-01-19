import pytest

from whistle.helpers import notify, strip_unwanted_chars
from whistle.models import Notification


@pytest.mark.django_db
class TestNotifyHelper:
    def test_notify_creates_notification(self, user, other_user):
        """Test notify helper creates notification."""
        initial_count = Notification.objects.count()

        notify(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user
        )

        assert Notification.objects.count() == initial_count + 1

    def test_notify_with_all_params(self, user, other_user):
        """Test notify helper with all parameters."""
        notify(
            recipient=user,
            event='TEST_EVENT',
            actor=other_user,
            object=user,
            target=other_user,
            details='Test details'
        )

        notification = Notification.objects.latest('created')
        assert notification.recipient == user
        assert notification.event == 'TEST_EVENT'
        assert notification.actor == other_user
        assert notification.details == 'Test details'

    def test_notify_without_optional_params(self, user):
        """Test notify helper without optional parameters."""
        notify(
            recipient=user,
            event='SIMPLE_EVENT'
        )

        notification = Notification.objects.latest('created')
        assert notification.recipient == user
        assert notification.event == 'SIMPLE_EVENT'
        assert notification.actor is None
        assert notification.object is None
        assert notification.target is None


class TestStripUnwantedChars:
    def test_strip_variable_placeholders(self):
        """Test stripping variable placeholders."""
        result = strip_unwanted_chars('Hello %(actor)s world')
        assert '%(actor)s' not in result
        assert 'Hello' in result
        assert 'world' in result

    def test_strip_quoted_placeholders(self):
        """Test stripping quoted variable placeholders."""
        result = strip_unwanted_chars('Hello "%(actor)s" world')
        assert '"%(actor)s"' not in result

    def test_strip_repr_placeholders(self):
        """Test stripping repr variable placeholders."""
        result = strip_unwanted_chars('Hello %(actor)r world')
        assert '%(actor)r' not in result

    def test_strip_empty_single_quotes(self):
        """Test stripping empty single quotes."""
        result = strip_unwanted_chars("Hello '' world")
        assert "''" not in result

    def test_strip_empty_double_quotes(self):
        """Test stripping empty double quotes."""
        result = strip_unwanted_chars('Hello "" world')
        assert '""' not in result

    def test_strip_empty_braces(self):
        """Test stripping empty braces."""
        result = strip_unwanted_chars('Hello () world')
        assert '()' not in result

    def test_strip_trailing_spaces(self):
        """Test stripping trailing spaces and colons."""
        result = strip_unwanted_chars('Hello world : ')
        assert not result.endswith(' ')
        assert not result.endswith(':')

    def test_strip_multiple_spaces(self):
        """Test stripping multiple spaces."""
        result = strip_unwanted_chars('Hello    world')
        assert '    ' not in result
        # Should have single space
        assert 'Hello world' == result

    def test_complex_string(self):
        """Test stripping complex string with multiple issues."""
        input_str = '%(actor)s sent "%(object)s" to %(target)s  : '
        result = strip_unwanted_chars(input_str)

        assert '%(actor)s' not in result
        assert '"%(object)s"' not in result
        assert '%(target)s' not in result
        assert '  ' not in result
        assert not result.endswith(':')
        assert not result.endswith(' ')

    def test_empty_string(self):
        """Test with empty string."""
        result = strip_unwanted_chars('')
        assert result == ''

    def test_no_changes_needed(self):
        """Test string that needs no changes."""
        input_str = 'Hello world'
        result = strip_unwanted_chars(input_str)
        assert result == 'Hello world'
