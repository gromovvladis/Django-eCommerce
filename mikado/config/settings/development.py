from .settings import *
from yookassa import Configuration

# =============
# DATABASES
# =============

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(__file__).resolve().parent.parent.parent / "db.sqlite",
        "USER": None,
        "PASSWORD": None,
        "HOST": None,
        "PORT": None,
        'ATOMIC_REQUESTS': True,
    }
}

# =============
# MIDDLEWARE
# =============

MIDDLEWARE += ['whitenoise.middleware.WhiteNoiseMiddleware']

# =============
# MEDIA
# =============

MEDIA_ROOT = location('public/media')

# =============
# COMPRESSOR
# =============

COMPRESS_ROOT = location('public/static/cache')
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False

# =============
# STATIC
# =============

STATIC_PRIVATE_ROOT = location('static')
ICON_DIR = location('static/svg')
STATICFILES_DIRS = (
    location('static'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# =============
# SECURE
# =============

ALLOWED_HOSTS = ("mikado-sushi.ru", "127.0.0.1")
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_REPLACE_HTTPS_REFERER = False
HOST_SCHEME = "http://"

SECRET_KEY='UtjFCuyjDKmWHe15neauXzHi2rZoRTg6RMbT5JyAdPiAcBP6Rra1'

# =============
# CACHES
# =============

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# =============
# SMS AERO
# =============

SMS_AUTH_SETTINGS["SMS_DEBUG"] = True
SMS_AUTH_SETTINGS["SMS_AUTH_PROVIDER_LOGIN"] = "s.gromovvladis@gmail.com"
SMS_AUTH_SETTINGS["SMS_AUTH_PROVIDER_API_TOKEN"] = "eZKAeSTM6ElHOWJ7Sry6sSSexq9R2faM"

# =============
# Yoomaney settings
# =============

Configuration.account_id = 470199
Configuration.secret_key = 'test_NbCwf5jnxkwJN7IzigODrtShMkQfsZRO_yU_SzEIa50'
# Configuration.secret_key = 'test_ty2zO4Cqfsodn0iGiAPDfOZ9E90X8bT1K2E6YYWyn6o'

# =============
# MAP settings
# =============

YANDEX_API_KEY = "27bbbf17-40e2-4c01-a257-9b145870aa2a"
GIS_API_KEY = "6013c28d-62ae-4764-a509-f403d2ee92c6"


# =============
# TRACING
# =============

GOOGLE_ANALYTICS_ID = None
YANDEX_ANALYTICS_ID = None


# =============
# TELEGRAM
# =============

TELEGRAM_BOT_TOKEN = "7440346552:AAH-k0ooubFF51xjcp3r-MIOkTAvnUF6F3I"
TELEGRAM_ADMINS_LIST = ("6560722014",)

# =============
# EVATOR
# =============

EVOTOR_TOKEN = "9179d780-56a4-49ea-b042-435e3257eaf6"