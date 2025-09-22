"""
Production settings for portfolio_backend project.
"""
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = False


# Security Settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database with connection pooling
import dj_database_url

DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL, 
            conn_max_age=600,
            conn_health_checks=True,
            options={
                'MAX_CONNS': 20,
                'MIN_CONNS': 5,
            }
        )
    }

# Static files - Use S3 or similar in real production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Sentry for error tracking
sentry_dsn = config('SENTRY_DSN', default=None)
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(auto_enabling=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=config('ENVIRONMENT', default='production'),
    )

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# Logging - Less verbose in production
LOGGING['handlers']['file']['filename'] = '/var/log/portfolio_backend/django.log'
LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['portfolio_backend']['level'] = 'INFO'

# Performance - Enable template caching
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]