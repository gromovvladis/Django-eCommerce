from .settings import *

# =============
# DATABASES
# =============

DATABASES = {
    "default": {
        "ENGINE": config("DATABASE_ENGINE"),
        "NAME": Path(__file__).resolve().parent.parent.parent / config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST"),
        "PORT": config("DATABASE_PORT"),
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
# STATIC
# =============

STATIC_PRIVATE_ROOT = location('static')
ICON_DIR = location('static/svg')
STATICFILES_DIRS = (
    location('static'),
)

# =============
# SECURE
# =============

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_REPLACE_HTTPS_REFERER = False
HOST_SCHEME = "http://"

SECRET_KEY='UtjFCuyjDKmWHe15neauXzHi2rZoRTg6RMbT5JyAdPiAcBP6Rra1'

# =============
# SMS AERO
# =============

SMS_AUTH_SETTINGS["SMS_DEBUG"] = True
SMS_AUTH_SETTINGS["SMS_AUTH_PROVIDER_LOGIN"] = "s.gromovvladis@gmail.com"
SMS_AUTH_SETTINGS["SMS_AUTH_PROVIDER_API_TOKEN"] = "eZKAeSTM6ElHOWJ7Sry6sSSexq9R2faM"

# =============
# Yoomaney settings
# =============

Configuration.account_id = 396529
Configuration.secret_key = 'test_ty2zO4Cqfsodn0iGiAPDfOZ9E90X8bT1K2E6YYWyn6o'

# =============
# MAP settings
# =============

YANDEX_API_KEY = "27bbbf17-40e2-4c01-a257-9b145870aa2a"
GIS_API_KEY = "6013c28d-62ae-4764-a509-f403d2ee92c6"