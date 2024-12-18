from .settings import *
from yookassa import Configuration

# =============
# SITE
# =============

PRIMARY_TITLE = "Доставка суши и роллов | Микадо Красноярск"

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
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = True

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

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-snowflake',
#     }
# }

# =============
# SMS AERO
# =============

SMS_AUTH_SETTINGS = {
    "SMS_CELERY_FILE_NAME": "run_celery",
    "SMS_AUTH_PROVIDER_FROM": "Mikado",
    "SMS_AUTH_MESSAGE": "Код для входа на сайт:",
    "SMS_DEBUG": True,
    "SMS_DEBUG_CODE": 1111,
    "SMS_AUTH_PROVIDER_URL": "https://gate.smsaero.ru/v2",
    "SMS_USER_SERIALIZER": "api.serializers.DefaultUserSerializer",
    "SMS_AUTH_PROVIDER_LOGIN": "s.gromovvladis@gmail.com",
    "SMS_AUTH_PROVIDER_API_TOKEN": "eZKAeSTM6ElHOWJ7Sry6sSSexq9R2faM",
}

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

TELEGRAM_STAFF_BOT_TOKEN = "7440346552:AAH-k0ooubFF51xjcp3r-MIOkTAvnUF6F3I"
TELEGRAM_ADMINS_LIST = ("6560722014",)

# =============
# EVATOR
# =============

EVOTOR_CLOUD_TOKEN = "1aa13792-abcf-40aa-8221-a78cfd702ea4"

EVOTOR_SITE_LOGIN = "evotor"
EVOTOR_SITE_PASS = "Evotormikadopassword25"
EVOTOR_SITE_TOKEN = "9179d780-56a4-49ea-b042-435e3257eaf7"
EVOTOR_SITE_USER_TOKEN = "9179d780-56a4-49ea-b042-435e3257eaf8"

MOBILE_CASHIER_LOGIN = ""
MOBILE_CASHIER_PASSWORD = ""
MOBILE_CASHIER_GROUP_CODE = ""

# =============
# CAMS
# =============

# CAMS_PASSWORD = "Mastersup25"

# =============
# EMAIL
# =============

# Registration
EMAIL_SUBJECT_PREFIX = 'Mikado'
OSCAR_FROM_EMAIL = "info@mikado-sushi.ru"
OSCAR_SEND_ORDER_PLACED_EMAIL = False
OSCAR_SEND_REGISTRATION_EMAIL = False

# Email
# EMAIL_USER=
# EMAIL_PASSWORD=