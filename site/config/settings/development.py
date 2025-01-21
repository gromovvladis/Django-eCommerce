from .settings import *
from yookassa import Configuration

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

ALLOWED_HOSTS = ("mikado-sushi.ru", "127.0.0.1", "localhost")
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

Configuration.account_id = 1017790
Configuration.secret_key = 'test_edf_VEetjIP5Yi4JDjvOsgzItD1whJpET4Px3nLIa6U'

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
TELEGRAM_CUSTOMER_BOT_TOKEN = None
TELEGRAM_SUPPORT_BOT_TOKEN = None
TELEGRAM_SUPPORT_CHAT_ID = 1001234567890

TELEGRAM_ADMINS_LIST = ("6560722014",)

# =============
# EVATOR
# =============

EVOTOR_CLOUD_TOKEN = "1aa13792-abcf-40aa-8221-a78cfd702ea4"

EVOTOR_SITE_LOGIN = "evotor"
EVOTOR_SITE_PASS = "Evotormikadopassword25"
EVOTOR_SITE_TOKEN = "9179d780-56a4-49ea-b042-435e3257eaf7"
EVOTOR_SITE_USER_TOKEN = "9179d780-56a4-49ea-b042-435e3257eaf8"

# =============
# WEBPUSH
# =============

WEBPUSH_PUBLIC_KEY = "BHuErJY5HcTiN8iGz5EOBgCP_vGhjrQmHhYMb81qP7hgmDm6IW2PmriE-GSVOOzlTLCqz5gbQKWhJc7R2OE437Q"
WEBPUSH_PRIVATE_KEY = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg6nb0Jg7856xHDcKr7sJ2d1s_XDQHRX6dS462Ge3Tf4yhRANCAAR7hKyWOR3E4jfIhs-RDgYAj_7xoY60Jh4WDG_Naj-4YJg5uiFtj5q4hPhklTjs5Uywqs-YG0CloSXO0djhON-0"
WEBPUSH_ADMIN_EMAIL = "s.gromovvladis@gmail.com"

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

# =============
# CAMS
# =============

# CAMS_PASSWORD = "Mastersup25"
