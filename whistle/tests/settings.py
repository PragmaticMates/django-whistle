"""
Django settings for running tests.
"""
import os

SECRET_KEY = 'test-secret-key-for-whistle-tests'

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'crispy_forms',
    'whistle',
    'whistle.tests',
]

AUTH_USER_MODEL = 'tests.TestUser'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ROOT_URLCONF = 'whistle.tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'whistle.middleware.ReadNotificationMiddleware',
]

USE_TZ = True

TIME_ZONE = 'UTC'

LANGUAGE_CODE = 'en-us'

USE_I18N = True

SITE_ID = 1

DEFAULT_FROM_EMAIL = 'test@example.com'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Whistle settings
WHISTLE_NOTIFICATION_EVENTS = (
    ('TEST_EVENT', '%(actor)s performed action on %(object)s'),
    ('SIMPLE_EVENT', 'A simple event occurred'),
    ('TARGET_EVENT', '%(actor)s sent %(object)s to %(target)s'),
)

WHISTLE_CHANNELS = ['web', 'email']

WHISTLE_USE_RQ = False

WHISTLE_SIGNING_KEY = 'test-signing-key'
WHISTLE_SIGNING_SALT = 'test-whistle-salt'
WHISTLE_AUTH_USER_MODEL = 'tests.TestUser'


# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
