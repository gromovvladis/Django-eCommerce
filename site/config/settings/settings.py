import os
from pathlib import Path

from decouple import config
from django.contrib.messages import constants as messages

from .defaults import *

# =============
# Path helper
# =============

BASE_DIR = Path(__file__).resolve().parent.parent

location = lambda x: os.path.join(os.path.dirname(BASE_DIR), x)

# =============
# DEBUG
# =============

DEBUG = config("DEBUG", default=False, cast=bool)
CELERY = config("CELERY", default=False, cast=bool)
INTERNAL_IPS = ["127.0.0.1", "::1"]

# =============
# MEDIA
# =============

MEDIA_URL = "media/"

# =============
# STATIC
# =============

STATIC_URL = "static/"

# =============
# TIME + LANG
# =============

TIME_ZONE = "Asia/Krasnoyarsk"
LANGUAGE_CODE = "ru"
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = "d E Y"
DATETIME_FORMAT = "d E Y H:i,"
LOCALE_PATHS = (location("locale"),)

# =============
# TEMPLATES
# =============

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            location("templates"),
        ],
        "OPTIONS": {
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                # Oscar specific
                "apps.webshop.search.context_processors.search_form",
                "apps.webshop.communication.notifications.context_processors.notifications",
                "core.context_processors.metadata",
            ],
            "debug": DEBUG,
        },
    }
]

# =============
# MIDDLEWARE
# =============

MIDDLEWARE = [
    # static
    "django.middleware.security.SecurityMiddleware",
    # django
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    # oscar
    "apps.webshop.middleware.WebshopMiddleware",
    "apps.dashboard.middleware.DashboardMiddleware",
]

if DEBUG:
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# =============
# APPS
# =============

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",
    "apps.webshop.apps.WebshopConfig",
    "apps.webshop.page.apps.PageConfig",
    "apps.webshop.action.apps.ActionConfig",
    "apps.webshop.analytics.apps.AnalyticsConfig",
    "apps.webshop.checkout.apps.CheckoutConfig",
    "apps.webshop.address.apps.AddressConfig",
    "apps.webshop.shipping.apps.ShippingConfig",
    "apps.webshop.catalogue.apps.CatalogueConfig",
    "apps.webshop.catalogue.reviews.apps.CatalogueReviewsConfig",
    "apps.webshop.communication.apps.CommunicationConfig",
    "apps.webshop.store.apps.StoreConfig",
    "apps.webshop.basket.apps.BasketConfig",
    "apps.webshop.payment.apps.PaymentConfig",
    "apps.webshop.offer.apps.OfferConfig",
    "apps.webshop.order.apps.OrderConfig",
    "apps.webshop.order.reviews.apps.OrderReviewsConfig",
    "apps.webshop.search.apps.SearchConfig",
    "apps.webshop.voucher.apps.VoucherConfig",
    "apps.webshop.wishlists.apps.WishlistsConfig",
    "apps.webshop.user.apps.UserConfig",
    "apps.webshop.user.customer.apps.CustomerConfig",
    "apps.dashboard.apps.DashboardMainConfig",
    "apps.dashboard.reports.apps.ReportsDashboardConfig",
    "apps.dashboard.users.apps.UsersDashboardConfig",
    "apps.dashboard.orders.apps.OrdersDashboardConfig",
    "apps.dashboard.catalogue.apps.CatalogueDashboardConfig",
    "apps.dashboard.offers.apps.OffersDashboardConfig",
    "apps.dashboard.stores.apps.StoresDashboardConfig",
    "apps.dashboard.pages.apps.PagesDashboardConfig",
    "apps.dashboard.ranges.apps.RangesDashboardConfig",
    "apps.dashboard.reviews.apps.ReviewsDashboardConfig",
    "apps.dashboard.vouchers.apps.VouchersDashboardConfig",
    "apps.dashboard.communications.apps.CommunicationsDashboardConfig",
    "apps.dashboard.shipping.apps.ShippingDashboardConfig",
    "apps.dashboard.payments.apps.PaymentsDashboardConfig",
    "apps.dashboard.evotor.apps.EvotorDashboardConfig",
    "apps.dashboard.telegram.apps.TelegramDashboardConfig",
    "apps.settings.apps.SettingsConfig",
    "apps.telegram.apps.TelegramConfig",
    "apps.evotor.apps.EvotorConfig",
    "apps.sms.apps.SmsConfig",
    "smsaero",  # sms
    "webpush",  # notif push
    "widget_tweaks",  # inputs
    "haystack",  # search
    "treebeard",  # thumbnail
    "sorl.thumbnail",
    "celery",  # celery
    "compressor",  # static
    "rest_framework",  # api
    "django_tables2",  # tables
    "django_celery_beat",
    "django_celery_results",
    "django.contrib.sitemaps",  # sitemap
]

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]

# =============
# AUTHENTICATION
# =============

AUTH_BACKEND = "apps.webshop.user.auth_backends.PhoneBackend"

AUTHENTICATION_BACKENDS = ("apps.webshop.user.auth_backends.PhoneBackend",)

LOGIN_REDIRECT_URL = "/"
APPEND_SLASH = True

# ====================
# Messages contrib app
# ====================

MESSAGE_TAGS = {messages.ERROR: "danger"}

# ====================
# SEARCH
# ====================

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": location("whoosh_index"),
        "INCLUDE_SPELLING": True,
    },
}

# ====================
# THUMBNAIL
# ====================

THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_FORMAT = "WEBP"
THUMBNAIL_COLORSPACE = None
THUMBNAIL_PRESERVE_FORMAT = True
THUMBNAIL_BACKEND = "sorl.thumbnail.base.ThumbnailBackend"
THUMBNAIL_KEY_PREFIX = "thumbnail"
THUMBNAIL_KVSTORE = config(
    "THUMBNAIL_KVSTORE", default="sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"
)

# ====================
# SECURITY
# ====================

SECURE_PROXY_SSL_HEADER = None
SECURE_HSTS_SECONDS = None
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_FRAME_DENY = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ====================
# SETTINGS
# ====================

ROOT_URLCONF = "config.urls"
SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = 1
