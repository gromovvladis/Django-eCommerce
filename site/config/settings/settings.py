import os
from pathlib import Path
from django.contrib.messages import constants as messages
from .defaults import *
from decouple import config

# =============
# Path helper
# =============

BASE_DIR = Path(__file__).resolve().parent.parent

location = lambda x: os.path.join(
    os.path.dirname(BASE_DIR), x)

# =============
# DEBUG
# =============

DEBUG = config("DEBUG", default=False, cast=bool)
TOOLBAR = config("TOOLBAR", default=False, cast=bool)
INTERNAL_IPS = ['127.0.0.1', '::1']

# =============
# MEDIA
# =============

MEDIA_URL = 'media/'

# =============
# STATIC
# =============

STATIC_URL = 'static/'

# =============
# TIME + LANG
# =============

# TIME_ZONE = 'Asia/Krasnoyarsk'
TIME_ZONE = 'Etc/GMT-7'
LANGUAGE_CODE = 'ru'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = 'd E Y'
LOCALE_PATHS = (location('locale'),)

# =============
# TEMPLATES
# =============

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            location('templates'),
        ],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                # Oscar specific
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.communication.notifications.context_processors.notifications',
                'oscar.core.context_processors.metadata',
            ],
            'debug': DEBUG,
        }
    }
]

# =============
# MIDDLEWARE
# =============

MIDDLEWARE = [
    # static
    'django.middleware.security.SecurityMiddleware',

    # django
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django.middleware.common.CommonMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',

    # oscar
    'oscar.apps.basket.middleware.BasketMiddleware',
    'oscar.apps.dashboard.middleware.DashboardMiddleware',
]

if TOOLBAR:
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# =============
# APPS
# =============

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',

    'config.settings.config.Shop',

    'oscar.apps.home.apps.HomeConfig',
    'oscar.apps.analytics.apps.AnalyticsConfig',
    'oscar.apps.checkout.apps.CheckoutConfig',
    'oscar.apps.address.apps.AddressConfig',
    'oscar.apps.shipping.apps.ShippingConfig',
    'oscar.apps.delivery.apps.DeliveryConfig',
    'oscar.apps.catalogue.apps.CatalogueConfig',
    'oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig',
    'oscar.apps.communication.apps.CommunicationConfig',
    'oscar.apps.store.apps.StoreConfig',
    'oscar.apps.basket.apps.BasketConfig',
    'oscar.apps.payment.apps.PaymentConfig',
    'oscar.apps.offer.apps.OfferConfig',
    'oscar.apps.order.apps.OrderConfig',
    'oscar.apps.customer.apps.CustomerConfig',
    'oscar.apps.search.apps.SearchConfig',
    'oscar.apps.voucher.apps.VoucherConfig',
    'oscar.apps.wishlists.apps.WishlistsConfig',
    'oscar.apps.telegram.apps.TelegramConfig',
    'oscar.apps.crm.apps.CRMConfig',
    'oscar.apps.sms_auth.apps.SmsConfig',
    'oscar.apps.user.apps.UserConfig',

    'oscar.apps.dashboard.apps.DashboardConfig',
    'oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    'oscar.apps.dashboard.users.apps.UsersDashboardConfig',
    'oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    'oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    'oscar.apps.dashboard.stores.apps.StoresDashboardConfig',
    'oscar.apps.dashboard.pages.apps.PagesDashboardConfig',
    'oscar.apps.dashboard.ranges.apps.RangesDashboardConfig',
    'oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig',
    'oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig',
    'oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig',
    'oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig',

    'oscar.apps.dashboard.payments.apps.PaymentsDashboardConfig',
    'oscar.apps.dashboard.crm.apps.CRMDashboardConfig',
    'oscar.apps.dashboard.delivery.apps.DeliveryDashboardConfig',
    'oscar.apps.dashboard.telegram.apps.TelegramDashboardConfig',

    'smsaero', #sms
    'webpush', # notif push
    'widget_tweaks', # inputs
    'haystack', # search
    'treebeard', # thumbnail
    'sorl.thumbnail',
    'compressor', # static
    'rest_framework', # api
    'django_tables2', # tables
    'celery', # celery
    'django_celery_beat',
    'django_celery_results',
    'django.contrib.sitemaps', # sitemap
]
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

# =============
# AUTHENTICATION
# =============

PHONE_BACKEND = "oscar.apps.user.auth_backends.PhoneBackend"

AUTHENTICATION_BACKENDS = (
    'oscar.apps.user.auth_backends.PhoneBackend',
)

LOGIN_REDIRECT_URL = '/'
APPEND_SLASH = True

# ====================
# Messages contrib app
# ====================

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

# ====================
# SEARCH
# ====================

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': location('whoosh_index'),
        'INCLUDE_SPELLING': True,
    },
}

# ====================
# THUMBNAIL
# ====================

THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_COLORSPACE = None
THUMBNAIL_PRESERVE_FORMAT = True
THUMBNAIL_BACKEND = 'sorl.thumbnail.base.ThumbnailBackend'
THUMBNAIL_KEY_PREFIX = 'mikado'
THUMBNAIL_KVSTORE = config('THUMBNAIL_KVSTORE', default='sorl.thumbnail.kvstores.cached_db_kvstore.KVStore')

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

ROOT_URLCONF = 'config.urls'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1
