# backend/settings/development.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Use local file storage for development
MEDIA_URL = '/dev_user_uploads/'
MEDIA_ROOT = BASE_DIR.parent / 'dev_user_uploads'

# Logging settings for development
USE_WATCHMAN = False
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',  # Capture all log messages
    },
    'loggers': {
        'backend': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Capture DEBUG and higher-level messages from your code
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Ensure all messages from your app are captured
            'propagate': False,
        },
    }
}

