from .settings import *

# =============
# SECURE
# =============

# SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CORS_REPLACE_HTTPS_REFERER = True
HOST_SCHEME = "https://"

SECRET_KEY='UtjFCuyjDKmWHe15neauXzHi2rZoRTg6RMbT5JyAdPiAcBP6Rra1'


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
        "OPTIONS": {
            "db": 10,
        },
    }
}

# MIDDLEWARE_PROD = [
#     "django.middleware.cache.UpdateCacheMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.cache.FetchFromCacheMiddleware"
# ]

# MIDDLEWARE.insert(0, MIDDLEWARE_PROD)


# =============
# CELERY
# =============

# CELERY_RESULT_BACKEND = 'redis://localhost:6379'
REDIS_URL = "redis://127.0.0.1:6379"
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXTENDED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
BROKER_URL = CELERY_BROKER_URL

# =============
# Yoomaney settings
# =============


Configuration.account_id = 396529
Configuration.secret_key = 'test_ty2zO4Cqfsodn0iGiAPDfOZ9E90X8bT1K2E6YYWyn6o'


# =============
# MEDIA
# =============

MEDIA_ROOT = location('public/media')

# =============
# STATIC
# =============

STATIC_URL = 'static/'
STATIC_ROOT = location('public/static')
STATICFILES_DIRS = (
    location('static'),
)


STATIC_PRIVATE_ROOT = location('public/static')
ICON_DIR = location('public/static/svg')


# =============
# DATABASES
# =============

DATABASES = {
    "default": {
        "ENGINE": config("DATABASE_ENGINE"),
        "NAME": config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST"),
        "PORT": config("DATABASE_PORT"),
        'ATOMIC_REQUESTS': True,
    }
}