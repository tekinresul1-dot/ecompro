"""
Django Development Settings

Extends base settings with development-specific configuration.
"""

from .base import *

# Debug mode ON for development
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Use console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Simplified logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# For development, use a fixed encryption key (NEVER do this in production!)
if not ENCRYPTION_KEY:
    # This is only for development - generate a proper key for production
    ENCRYPTION_KEY = 'dev-only-encryption-key-change-in-prod'

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable password validators in development for easier testing
AUTH_PASSWORD_VALIDATORS = []

# Optional: Use SQLite for quick development without PostgreSQL
# Enable SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
