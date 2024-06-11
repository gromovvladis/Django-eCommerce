from .settings import *

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
# MEDIA
# =============

MEDIA_ROOT = location("public/media")


# =============
# Yoomaney settings
# =============

Configuration.account_id = 396529
Configuration.secret_key = 'test_xWpaTgVQo-SeX7cgxtpX0iJZ76M-v9Zyam82yOgKa9M'
