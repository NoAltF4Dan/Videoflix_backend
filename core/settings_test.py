import os
from .settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'app_test',
        'USER': 'app_user',
        'PASSWORD': 'secret',
        'HOST': 'db',
        'PORT': '5432',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

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
        'level': 'WARNING',
    },
}

REDIS_URL = 'redis://redis:6379/2'

CACHES = {
    "default":
        {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

RQ_QUEUES = {
    'default': {
        'HOST': os.environ.get("REDIS_HOST", default="redis"),
        'PORT': os.environ.get("REDIS_PORT", default=6379),
        'DB': 2,  # Tests use DB 2
        'DEFAULT_TIMEOUT': 900,
        'REDIS_CLIENT_KWARGS': {},
    },
}

DEBUG = True

COOKIE_DOMAIN = None

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
