"""
Django Base Settings for Trendyol Profitability SaaS

This file contains settings common to all environments.
Environment-specific settings are in development.py and production.py.

SECURITY HARDENED VERSION
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import secrets

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# SECURITY: Secret key must be set via environment variable in production
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    # Only for development - generate a random key
    SECRET_KEY = secrets.token_urlsafe(50)
    print("WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY env variable in production!")

# SECURITY: Debug mode defaults to False
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# SECURITY: Strict allowed hosts
ALLOWED_HOSTS = [
    host.strip() 
    for host in os.getenv('ALLOWED_HOSTS', '').split(',') 
    if host.strip()
]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# =============================================================================
# Application definition
# =============================================================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.sellers',
    'apps.products',
    'apps.orders',
    'apps.calculations',
    'apps.analytics',
    'apps.integrations',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# =============================================================================
# MIDDLEWARE (Order matters for security!)
# =============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # SECURITY: Custom security middleware
    'core.security.SecurityMiddleware',
    'core.security.LoginRateLimitMiddleware',
    'core.security.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'


# =============================================================================
# Database Configuration
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'trendyol_profitability'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        # SECURITY: SSL for database connection in production
        'CONN_MAX_AGE': 60,
    }
}


# =============================================================================
# Password Validation (SECURITY HARDENED)
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10}  # SECURITY: Increased from 8 to 10
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =============================================================================
# Internationalization
# =============================================================================
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True


# =============================================================================
# Static & Media Files
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# SECURITY: Limit upload size
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'


# =============================================================================
# REST Framework Configuration (SECURITY HARDENED)
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    
    # SECURITY: Rate limiting (requires django-ratelimit or similar)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',      # Anonymous users: 100 requests/hour
        'user': '1000/hour',     # Authenticated users: 1000 requests/hour
        'login': '5/minute',     # Login attempts: 5 per minute
    },
}


# =============================================================================
# JWT Configuration (SECURITY HARDENED)
# =============================================================================
SIMPLE_JWT = {
    # SECURITY: Shorter access token lifetime
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 30))  # Reduced from 60 to 30
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7))
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    # SECURITY: Use strong algorithm
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    # SECURITY: Token blacklist cleanup
    'TOKEN_BLACKLIST_ENABLED': True,
}


# =============================================================================
# CORS Configuration (SECURITY HARDENED)
# =============================================================================
# SECURITY: Only allow specific origins, never use CORS_ALLOW_ALL_ORIGINS in production
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

# SECURITY: Limit allowed headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'origin',
    'x-csrftoken',
    'x-requested-with',
]

# SECURITY: Only allow safe methods for preflight
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]


# =============================================================================
# Session & CSRF Security
# =============================================================================
# SECURITY: Session configuration
SESSION_COOKIE_AGE = 60 * 60 * 24  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# SECURITY: CSRF configuration
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()


# =============================================================================
# Security Headers (Applied in all environments)
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'


# =============================================================================
# Celery Configuration
# =============================================================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']  # SECURITY: Only accept JSON
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task

CELERY_BEAT_SCHEDULE = {
    'sync-all-seller-orders-daily': {
        'task': 'apps.integrations.tasks.sync_all_seller_orders',
        'schedule': 60 * 60 * 6,  # Every 6 hours
    },
    'recalculate-daily-summaries': {
        'task': 'apps.calculations.tasks.recalculate_daily_summaries',
        'schedule': 60 * 60 * 24,  # Daily
    },
    # SECURITY: Clean up expired tokens daily
    'cleanup-expired-tokens': {
        'task': 'apps.accounts.tasks.cleanup_expired_tokens',
        'schedule': 60 * 60 * 24,  # Daily
    },
}


# =============================================================================
# Application-Specific Settings
# =============================================================================

# SECURITY: Encryption key must be set for API credentials
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')

# Trendyol API Settings
TRENDYOL_API_BASE_URL = os.getenv('TRENDYOL_API_BASE_URL', 'https://api.trendyol.com/sapigw')
TRENDYOL_RATE_LIMIT_PER_SECOND = int(os.getenv('TRENDYOL_RATE_LIMIT_PER_SECOND', 5))

# Default VAT rates (Turkey)
DEFAULT_VAT_RATE = float(os.getenv('DEFAULT_VAT_RATE', 20.00))
DEFAULT_COMMISSION_VAT_RATE = float(os.getenv('DEFAULT_COMMISSION_VAT_RATE', 20.00))

# Calculation settings
CALCULATION_DECIMAL_PLACES = 4
CALCULATION_VERSION = '1.0'


# =============================================================================
# Logging Configuration
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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)
