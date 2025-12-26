"""
Django Production Settings

Extends base settings with production-specific configuration.
MAXIMUM SECURITY settings for live deployment.
"""

import os
from .base import *

# =============================================================================
# CRITICAL SECURITY CHECKS
# =============================================================================

# Debug mode MUST be OFF in production
DEBUG = False

# Secret key MUST be set
if SECRET_KEY == 'django-insecure-change-this-in-production' or len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be set to a secure, random value in production!")

# Encryption key is MANDATORY
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY must be set in production!")

# Allowed hosts MUST be configured
ALLOWED_HOSTS = [
    host.strip() 
    for host in os.getenv('ALLOWED_HOSTS', '').split(',') 
    if host.strip()
]
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be set in production!")


# =============================================================================
# HTTPS/SSL SECURITY
# =============================================================================
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'


# =============================================================================
# SECURITY HEADERS
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy (add django-csp for more control)
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'


# =============================================================================
# DATABASE SECURITY
# =============================================================================
# SECURITY: Use SSL for database connection
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'sslmode': os.getenv('DB_SSL_MODE', 'prefer'),
}


# =============================================================================
# CORS SECURITY
# =============================================================================
# SECURITY: Never allow all origins in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]

if not CORS_ALLOWED_ORIGINS:
    raise ValueError("CORS_ALLOWED_ORIGINS must be set in production!")


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')


# =============================================================================
# RATE LIMITING (ENHANCED FOR PRODUCTION)
# =============================================================================
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '50/hour',       # Stricter for production
    'user': '500/hour',      # Stricter for production
    'login': '3/minute',     # Prevent brute force
}


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


# =============================================================================
# PRODUCTION LOGGING
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': 'SECURITY {levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'security',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# =============================================================================
# JWT SECURITY (STRICTER FOR PRODUCTION)
# =============================================================================
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=15)  # Shorter in production
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)     # Shorter in production


# =============================================================================
# ADDITIONAL SECURITY MEASURES
# =============================================================================

# Admin URL should be changed from default
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

# Maximum request body size
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB - stricter in production
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# Session timeout
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours instead of 24
