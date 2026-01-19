# django-whistle

Django Whistle is a Django app that provides a flexible, multi-channel notification system.
Supports `web` (in-app), `email`, and `push` (FCM) channels with user preferences and background job processing.

## Installation

```bash
pip install django-whistle
```

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'whistle',
    'fcm_django',  # only if using push notifications
]
```

Run migrations:

```bash
python manage.py migrate whistle
```

## Configuration

### Events and Channels

Define notification events and enable channels in your `settings.py`:

```python
from django.utils.translation import gettext_lazy as _

WHISTLE_CHANNELS = ['web', 'push', 'email']
WHISTLE_NOTIFICATION_EVENTS = (
    ('ORDER_PLACED', _('%(actor)s placed order %(object)s')),
    ('ORDER_SHIPPED', _('Your order %(object)s has been shipped')),
)
```

Template variables: `%(actor)s`, `%(object)s`, `%(target)s`

### User Model Integration

Add the mixin to your User model for notification preferences and unread counts:

```python
from whistle.mixins import UserNotificationsMixin

class User(UserNotificationsMixin, AbstractUser):
    pass
```

### URL Configuration

```python
from django.urls import path, include

urlpatterns = [
    path('notifications/', include('whistle.urls')),
]
```

This provides:
- `notifications:list` - Notification list view
- `notifications:settings` - User preference management
- `notifications:read_notification` - Mark notification as read via signed hash

### Middleware

Add `ReadNotificationMiddleware` to automatically mark notifications as read:

```python
MIDDLEWARE = [
    # ...
    'whistle.middleware.ReadNotificationMiddleware',
]
```

The middleware provides two features:

1. **URL parameter tracking** - Marks a notification as read when the URL contains the `read-notification` query parameter (configurable via `WHISTLE_URL_PARAM`) with the notification ID.

2. **DetailView auto-marking** - Automatically marks all unread notifications as read when a user views a `DetailView` of an object that is related to the notification (either as `object` or `target`).

### Custom Managers and Handlers

Override notification logic by creating custom managers or handlers:

```python
# settings.py

WHISTLE_AVAILABILITY_HANDLER = "myapp.handlers.availability_handler"
WHISTLE_NOTIFICATION_MANAGER_CLASS = "myapp.managers.CustomNotificationManager"
WHISTLE_EMAIL_MANAGER_CLASS = "myapp.managers.CustomEmailManager"
```

### Asynchronous Notifications

Enable background processing with django-rq:

```python
# settings.py

WHISTLE_USE_RQ = True
WHISTLE_REDIS_QUEUE = 'default'

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    }
}
```

### All Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `WHISTLE_NOTIFICATION_EVENTS` | `[]` | Tuple of (event_name, template_string) pairs |
| `WHISTLE_CHANNELS` | `['web', 'email']` | Enabled notification channels |
| `WHISTLE_AVAILABILITY_HANDLER` | `None` | Path to custom availability function |
| `WHISTLE_URL_HANDLER` | `None` | Path to custom URL generation function |
| `WHISTLE_URL_PARAM` | `'read-notification'` | Query parameter for marking notifications read |
| `WHISTLE_CACHE_TIMEOUT` | `DEFAULT_TIMEOUT` | Cache duration (Django's default) |
| `WHISTLE_USE_RQ` | `True` | Enable background job processing |
| `WHISTLE_REDIS_QUEUE` | `'default'` | Redis queue name for background jobs |
| `WHISTLE_SIGNING_KEY` | `SECRET_KEY` | Key for signing notification hashes |
| `WHISTLE_SIGNING_SALT` | `'whistle'` | Salt for signing notification hashes |
| `WHISTLE_AUTH_USER_MODEL` | `AUTH_USER_MODEL` | Custom user model |
| `WHISTLE_OLD_THRESHOLD` | `None` | Age threshold for old notifications (timedelta) |
| `WHISTLE_DEFAULT_NOTIFICATIONS` | `{}` | Default channel/event settings |
| `WHISTLE_NOTIFICATION_MANAGER_CLASS` | `'whistle.managers.NotificationManager'` | Custom notification manager |
| `WHISTLE_EMAIL_MANAGER_CLASS` | `'whistle.managers.EmailManager'` | Custom email manager |

## Usage

### Sending Notifications

```python
from whistle.helpers import notify

notify(
    recipient=user,
    event='ORDER_PLACED',
    actor=request.user,
    object=order,
    target=None,
    details='Additional context',
)
```

### Email Templates

Create event-specific email templates at `templates/whistle/mails/{event_name}.txt`.
Falls back to `templates/whistle/mails/new_notification.txt`.

### Management Commands

```bash
# Delete old notifications
python manage.py delete_old_notifications [--dry-run]

# Copy notification settings between channels
python manage.py copy_channel_settings <from_channel> <to_channel> [--delete]
```

## REST API

If using Django REST Framework, the package provides:
- `NotificationViewSet` - Read-only viewset for user notifications
- `MarkNotificationsAsReadAPIView` - PATCH endpoint to mark notifications as read

## Managers

### NotificationQuerySet

Custom queryset with filtering methods for notifications:

| Method | Description |
|--------|-------------|
| `unread()` | Filter unread notifications |
| `mark_as_read()` | Bulk update notifications as read |
| `for_recipient(user)` | Filter by recipient user |
| `of_object(obj)` | Filter by related object |
| `of_target(target)` | Filter by target object |
| `of_object_or_target(obj)` | Filter by either object or target |
| `old(threshold)` | Filter notifications older than threshold |
| `not_old(threshold)` | Filter notifications newer than threshold |

### NotificationManager

Handles notification creation and dispatch logic. Key methods:

| Method | Description |
|--------|-------------|
| `notify(recipient, event, actor, object, target, details)` | Create and dispatch notification to enabled channels |
| `is_channel_available(user, channel)` | Check if channel is available for user |
| `is_notification_enabled(user, channel, event)` | Check if notification is enabled (availability + user preferences) |
| `get_description(event, actor, object, target)` | Render notification text from event template |
| `get_push_config(notification)` | Build FCM push notification configuration |
| `push_notification(notification)` | Send push notification via FCM |
| `mail_notification(notification)` | Trigger email notification |

Signals emitted:
- `notification_emailed` - Sent after email notification is dispatched
- `notification_pushed` - Sent after push notification is dispatched

### EmailManager

Handles email notification rendering and sending:

| Method | Description |
|--------|-------------|
| `send_mail(recipient, event, **kwargs)` | Send email notification (sync or via RQ) |
| `prepare_email(recipient, event, **kwargs)` | Build email subject, message, and HTML content |
| `load_template(template_type, recipient, event)` | Load event-specific or default template |
| `get_mail_subject(context)` | Generate subject with site name prefix |
| `get_mail_context(recipient, event, **kwargs)` | Build template context with descriptions |

## Background Jobs

When `WHISTLE_USE_RQ=True`, notifications and emails are processed asynchronously via django-rq:

| Job | Description |
|-----|-------------|
| `notify_in_background(recipient, event, ...)` | Queue notification creation |
| `send_mail_in_background(subject, message, ...)` | Queue email sending |

Jobs are dispatched to the queue specified by `WHISTLE_REDIS_QUEUE` (default: `'default'`).

## Versioning

We use [SemVer](http://semver.org/) for versioning.

## Authors

* **Erik Telepovský** - [Pragmatic Mates](https://github.com/pragmaticmates)

See also the list of [contributors](https://github.com/pragmaticmates/django-whistle/contributors).

## License

This project is licensed under the BSD License - see the [LICENSE](LICENSE) file for details.
