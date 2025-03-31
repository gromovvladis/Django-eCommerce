from yookassa import Configuration

from .settings import *

# =============
# MULTI STORES
# =============

DELIVERY_AVAILABLE = True
STORE_SELECT = True
STORE_DEFAULT = 1

# =============
# COMPANY
# =============

# 1	Общая система налогообложения
# 2	Упрощенная (УСН, доходы)
# 3	Упрощенная (УСН, доходы минус расходы)
# 4	Единый налог на вмененный доход (ЕНВД)
# 5	Единый сельскохозяйственный налог (ЕСН)
# 6	Патентная система налогообложения
TAX_SYSTEM = 2

# =============
# SITE
# =============

PRIMARY_TITLE = "Доставка суши и роллов | Микадо Красноярск"
SUPPORT_LINK = "#"

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
        "ATOMIC_REQUESTS": True,
    }
}

# =============
# MIDDLEWARE
# =============

MIDDLEWARE += ["whitenoise.middleware.WhiteNoiseMiddleware"]

# =============
# MEDIA
# =============

MEDIA_ROOT = location("public/media")

# =============
# COMPRESSOR
# =============

COMPRESS_ROOT = location("public/static/cache")
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = True

# =============
# STATIC
# =============

STATIC_PRIVATE_ROOT = location("static")
ICON_DIR = location("static/svg")
STATICFILES_DIRS = (location("static"),)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

# =============
# SECURE
# =============

ALLOWED_HOSTS = ("mikado-sushi.ru", "127.0.0.1", "localhost")
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_REPLACE_HTTPS_REFERER = False
HOST_SCHEME = "http://"

SECRET_KEY = ""

# =============
# CACHES
# =============

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-snowflake',
#     }
# }

# =============
# CELERY
# =============

CELERY_LOGGER_NAME = "celery"
CELERY_BROKER_URL = None
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# =============
# SMS AERO
# =============

SMS_AUTH_SETTINGS = {
    "SMS_CELERY_FILE_NAME": "run_celery",
    "SMS_AUTH_PROVIDER_FROM": "Mikado",
    "SMS_AUTH_MESSAGE": "Код для входа на сайт:",
    "SMS_DEBUG": True,
    "SMS_DEBUG_CODE": 1234,
    "SMS_AUTH_PROVIDER_URL": "https://gate.smsaero.ru/v2",
    "SMS_USER_SERIALIZER": "api.serializers.DefaultUserSerializer",
    "SMS_AUTH_PROVIDER_LOGIN": "",
    "SMS_AUTH_PROVIDER_API_TOKEN": "",
}

# =============
# Yoomaney settings
# =============

Configuration.account_id = ""
Configuration.secret_key = ""

# =============
# MAP settings
# =============

YANDEX_API_KEY = ""
GIS_API_KEY = ""

# =============
# TRACING
# =============

GOOGLE_ANALYTICS_ID = None
YANDEX_ANALYTICS_ID = None

# =============
# TELEGRAM
# =============

TELEGRAM_STAFF_BOT_TOKEN = ""
TELEGRAM_CUSTOMER_BOT_TOKEN = None
TELEGRAM_SUPPORT_BOT_TOKEN = None
TELEGRAM_SUPPORT_CHAT_ID = "

TELEGRAM_ADMINS_LIST = ("",)

# =============
# EVATOR
# =============

EVOTOR_CLOUD_TOKEN = ""

EVOTOR_SITE_LOGIN = ""
EVOTOR_SITE_PASS = ""
EVOTOR_SITE_TOKEN = ""
EVOTOR_SITE_USER_TOKEN = ""

# =============
# WEBPUSH
# =============

WEBPUSH_PUBLIC_KEY = "BHuErJY5HcTiN8dfgdfgdfgdqP7hgmDm6IW2PmriE-GSVOOzlTLCqz5gbQKWhJc7R2OE437Q"
WEBPUSH_PRIVATE_KEY = "MIdfgdfgdfgdfgjyjndrgtM49AwEHBG0wawIBAQQg6nb0Jg7856xHDcKr7sJ2d1s_XDQHRX6dS462Ge3Tf4yhRANCAAR7hKyWOR3E4jfIhs-RDgYAj_7xoY60Jh4WDG_Naj-4YJg5uiFtj5q4hPhklTjs5Uywqs-YG0CloSXO0djhON-0"
WEBPUSH_ADMIN_EMAIL = "s.gromovvladis@gmail.com"

# =============
# EMAIL
# =============

# Registration
EMAIL_SUBJECT_PREFIX = "Mikado"
FROM_EMAIL = "info@mikado-sushi.ru"
SEND_ORDER_PLACED_EMAIL = False
SEND_REGISTRATION_EMAIL = False
