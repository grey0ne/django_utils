
import django_stubs_ext

from dataorm.settings_helpers import config_get, config_get_str
from typing import Any
from copy import deepcopy
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import sys

django_stubs_ext.monkeypatch()

PROJECT_DOMAIN = config_get_str('PROJECT_DOMAIN')
PROJECT_NAME = config_get_str('PROJECT_NAME')
PROJECT_VERSION = config_get_str('PROJECT_VERSION', '0')

ROOT_URLCONF = 'application.urls'
WSGI_APPLICATION = 'application.wsgi.application'

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

SOURCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(SOURCE_DIR)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

POOL_OPTIONS: dict[str, int] = {
    "min_size": 2,  # Minimum number of connections in the pool
    "max_size": 4,  # Maximum number of connections in the pool
    "timeout": 10,  # Timeout in seconds for acquiring a connection
}

if 'migrate' in sys.argv:
    db_options = {}
else:
    db_options: dict[str, Any] = {
        "options": "-c statement_timeout=500",
        "pool": POOL_OPTIONS
    } 


DATABASES: dict[str, Any] = {
    "default": {
        "NAME": config_get_str('DATABASE_NAME', default=PROJECT_NAME),
        "USER": config_get_str('DATABASE_USER', default=PROJECT_NAME),
        "HOST": config_get_str('DATABASE_HOST', default=f'{PROJECT_NAME}-postgres'),
        "PORT": config_get_str('DATABASE_PORT', default='5432'),
        "PASSWORD": config_get_str('DATABASE_PASSWORD', default=PROJECT_NAME),
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": db_options
    }
}

AUTHENTICATION_BACKENDS = (
    'application.backends.AsyncModelBackend',
)

MIDDLEWARE = [
    'dataorm.middleware.DomainRoutingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [f'https://{PROJECT_DOMAIN}', ]

DEBUG = bool(config_get('DJANGO_DEBUG', default=False)) # type: ignore

SECRET_KEY = config_get_str('DJANGO_SECRET_KEY')

extra_domains_str = config_get_str('EXTRA_DOMAINS', default='')

EXTRA_DOMAINS: list[str] = extra_domains_str.split(',') if len(extra_domains_str) > 0 else []

ALLOWED_HOSTS: list[str] = [
    f'{PROJECT_NAME}-django',
    PROJECT_DOMAIN,
] + EXTRA_DOMAINS


# URL prefix is needed in development
DEFAULT_MEDIA_DOMAIN = f'media.{PROJECT_DOMAIN}/{PROJECT_NAME}-media' if DEBUG else f'media.{PROJECT_DOMAIN}'
DEFAULT_S3_KEY = f'{PROJECT_NAME}_minio' if DEBUG else None
DEFAULT_S3_SECRET = f'{PROJECT_NAME}_minio' if DEBUG else None
DEFAULT_S3_SIGNATURE = 's3' if DEBUG else 'v4'


S3_ACCESS_KEY_ID = config_get("S3_ACCESS_KEY_ID", default=DEFAULT_S3_KEY)
S3_SECRET_KEY = config_get("S3_SECRET_KEY", default=DEFAULT_S3_SECRET)
S3_ENDPOINT = config_get("S3_ENDPOINT_URL", default=f'http://{PROJECT_NAME}-minio:9000')
S3_MEDIA_DOMAIN = config_get("S3_MEDIA_DOMAIN", default=DEFAULT_MEDIA_DOMAIN)
S3_STATIC_DOMAIN = config_get("S3_STATIC_DOMAIN", default=f'static.{PROJECT_DOMAIN}')
S3_SIGNATURE_VERSION = config_get("S3_SIGNATURE_VERSION", default=DEFAULT_S3_SIGNATURE)
S3_ACL = config_get("S3_ACL", default='private')
S3_MEDIA_BUCKET = config_get("S3_MEDIA_BUCKET", default=f'{PROJECT_NAME}-media')
S3_STATIC_BUCKET = config_get("S3_STATIC_BUCKET", default=f'{PROJECT_NAME}-static')

STATIC_URL = '/static/' if DEBUG else f'https://{S3_STATIC_DOMAIN}/'

MEDIA_S3_STORAGE: dict[str, Any] = {
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {
        'bucket_name': S3_MEDIA_BUCKET,
        'endpoint_url': S3_ENDPOINT,
        'access_key': S3_ACCESS_KEY_ID,
        'secret_key': S3_SECRET_KEY,
        'default_acl': S3_ACL,
        'location': '',
        'signature_version': S3_SIGNATURE_VERSION,
        'file_overwrite': True,
        'querystring_auth': S3_ACL == 'private',
        'querystring_expire': 60 * 2,  # Links valid for two minutes
        'custom_domain': S3_MEDIA_DOMAIN,
    },
}

STATIC_S3_STORAGE: dict[str, Any] = deepcopy(MEDIA_S3_STORAGE)
STATIC_S3_STORAGE['OPTIONS']['default_acl'] = 'public-read'
STATIC_S3_STORAGE['OPTIONS']['querystring_auth'] = False
STATIC_S3_STORAGE['OPTIONS']['custom_domain'] = S3_STATIC_DOMAIN
STATIC_S3_STORAGE['OPTIONS']['bucket_name'] = S3_STATIC_BUCKET

LOCAL_STATIC_STORAGE: dict[str, Any] = { "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" }

STATIC_ROOT = os.path.join(SOURCE_DIR, 'collected_static')

STORAGES: dict[str, Any] = {
    "default": MEDIA_S3_STORAGE,
    "staticfiles": LOCAL_STATIC_STORAGE
}

TEMPLATES: list[dict[str, Any]] = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(SOURCE_DIR, 'templates') ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]


VERSION = PROJECT_VERSION

SITE_URL = f'https://{PROJECT_DOMAIN}'

SENTRY_FRONTEND_DSN = config_get('SENTRY_FRONTEND_DSN', default=None)

SENTRY_DSN = config_get('SENTRY_DSN', default=None)
if SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=str(SENTRY_DSN),
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        release=PROJECT_VERSION
    )

SESSION_COOKIE_SECURE = not DEBUG

LOGIN_REDIRECT_URL = '/'
AUTH_USER_MODEL = 'users.User'

SESSION_COOKIE_AGE = 31622400 * 4  # 4 Years
