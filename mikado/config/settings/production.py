from .settings import *

# =============
# SECURE
# =============

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CORS_REPLACE_HTTPS_REFERER = True
HOST_SCHEME = "https://"

SECRET_KEY='UtjFCuyjDKmWHe25neauXzHi2eZoRXg6RMbT5JyAdPiAcBP6Rra1'


# =============
# Redis
# =============

REDIS_BACKEND = 'redis://localhost:6379'
THUMBNAIL_REDIS_URL = 'redis://localhost:6379'

# =============
# CACHE
# =============

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://@127.0.0.1:6379",
        "TIMEOUT": 6000,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
            "username": "user",
            "password": "pass",
            "pool_class": "redis.BlockingConnectionPool",
        },
    }
}

MIDDLEWARE += [
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware"
]


# =============
# CELERY
# =============

# CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXTENDED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

# =============
# Yoomaney settings
# =============

Configuration.account_id = 396529
Configuration.secret_key = 'test_xWpaTgVQo-SeX7cgxtpX0iJZ76M-v9Zyam82yOgKa9M'
