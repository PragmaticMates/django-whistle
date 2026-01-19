# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**django-whistle** is a Django app providing a multi-channel notification system supporting web (in-app), email, and push notifications. Version 6.0.1, licensed under BSD.

## Development Commands

```bash
# Install in development mode
pip install -e .

# Build package
python setup.py sdist bdist_wheel

# Run migrations
python manage.py migrate whistle

# Management commands
python manage.py delete_old_notifications [--dry-run]
python manage.py copy_channel_settings <from_channel> <to_channel> [--delete]
```

Note: No test suite is configured in this repository.

## Architecture

### Core Flow
1. **notify()** helper (or NotificationManager.notify) is called with recipient, event, actor, object, target, details
2. Channel/event availability is checked via global settings, AVAILABILITY_HANDLER, and user preferences
3. Notifications dispatched to enabled channels: web (database), email, push (FCM)
4. Background processing via django_rq if WHISTLE_USE_RQ=True

### Key Modules

| Module | Purpose |
|--------|---------|
| `managers.py` | NotificationManager (creation logic), EmailManager, NotificationQuerySet |
| `models.py` | Notification model with GenericForeignKey relations to object/target |
| `mixins.py` | UserNotificationsMixin - add to User model for notification_settings JSON field and unread count caching |
| `middleware.py` | ReadNotificationMiddleware - auto-marks notifications read via URL param or DetailView |
| `jobs.py` | Background tasks: notify_in_background(), send_mail_in_background() |
| `settings.py` | All WHISTLE_* setting definitions with defaults |

### Customization Points
- `WHISTLE_AVAILABILITY_HANDLER` - Function to control channel/event access per user
- `WHISTLE_URL_HANDLER` - Custom URL generation for notifications
- `WHISTLE_NOTIFICATION_MANAGER_CLASS` - Override NotificationManager
- `WHISTLE_EMAIL_MANAGER_CLASS` - Override EmailManager
- Event-specific email templates: `whistle/mails/{event_name}.txt` (falls back to `new_notification.txt`)

### Event System
Events defined as tuples with template strings supporting variables:
```python
WHISTLE_NOTIFICATION_EVENTS = (
    ('ORDER_PLACED', '%(actor)s placed order %(object)s'),
)
```
Variables: `%(actor)s`, `%(object)s`, `%(target)s`

### Dependencies
- **Required**: django>=3, django_rq, django-crispy-forms, django-pragmatic>=4.1.0
- **Conditional**: fcm_django (if 'push' channel enabled)
- **Optional**: djangorestframework (for API endpoints)

## URL Namespace

App name: `notifications`
- `notifications:list` - Notification list view
- `notifications:settings` - User preference management
- `notifications:read_notification` - Email click tracking with signed hash
