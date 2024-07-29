from pathlib import Path
import os
from django.contrib.messages import constants as messages
from .defaults import *
from decouple import config
from datetime import datetime

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

TIME_ZONE = 'Asia/Krasnoyarsk'
LANGUAGE_CODE = 'ru'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = 'd E Y'

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
                # 'django.template.context_processors.debug'
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
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',

    # oscar
    'oscar.apps.basket.middleware.BasketMiddleware',
]

if DEBUG:
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# =============
# LOGGING
# =============

if not DEBUG:
    LOG_DIR = location('logs')
    LOG_FILE = '/logs_' + datetime.now().strftime("%Y-%m-%d_%H-%M") + ".log"
    LOG_PATH = LOG_DIR + LOG_FILE

    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)

    if not os.path.exists(LOG_PATH):
        f = open(LOG_PATH, 'a').close() #create empty log file
    else:
        f = open(LOG_PATH,"w").close()

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
            },
            'simple': {
                'format': '[%(asctime)s] %(message)s'
            },
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'handlers': {
            'null': {
                'level': 'DEBUG',
                'class': 'logging.NullHandler',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'formatter': 'verbose',
                'filename': LOG_PATH,
                'encoding': 'UTF-8',
            },
        },
        'loggers': {
            'oscar': {
                'level': 'DEBUG',
                'propagate': True,
            },
            'oscar.catalogue.import': {
                'handlers': ['console','file'],
                'level': 'INFO',
                'propagate': False,
            },
            'oscar.alerts': {
                'handlers': ['null','file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            # Django loggers
            'django': {
                'handlers': ['null', 'file'],
                'propagate': True,
                'level': 'INFO',
            },
            'django': {
                'handlers': ['file'],
                'propagate': True,
                'level': 'ERROR',
            },
            'django': {
                'handlers': ['file'],
                'propagate': True,
                'level': 'WARNING',
            },
            'django.request': {
                'handlers': ['console','file'],
                'level': 'ERROR',
                'propagate': True,
            },
            'django.db.backends': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': True,
            },
            'django.security.DisallowedHost': {
                'handlers': ['null','file'],
                'propagate': False,
            },

            # Third party
            'raven': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False,
            },
            'sorl.thumbnail': {
                'handlers': ['console', 'file'],
                'propagate': True,
                'level': 'INFO',
            },
        }
    }

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
    'oscar.apps.partner.apps.PartnerConfig',
    'oscar.apps.basket.apps.BasketConfig',
    'oscar.apps.payment.apps.PaymentConfig',
    'oscar.apps.offer.apps.OfferConfig',
    'oscar.apps.order.apps.OrderConfig',
    'oscar.apps.customer.apps.CustomerConfig',
    'oscar.apps.search.apps.SearchConfig',
    'oscar.apps.voucher.apps.VoucherConfig',
    'oscar.apps.wishlists.apps.WishlistsConfig',

    'oscar.apps.dashboard.apps.DashboardConfig',
    'oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    'oscar.apps.dashboard.users.apps.UsersDashboardConfig',
    'oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    'oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    'oscar.apps.dashboard.partners.apps.PartnersDashboardConfig',
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

    #vlad
    'smsaero',
    'apps.sms_auth.apps.SmsConfig',
    'apps.user.apps.UserConfig',

    # 3rd-party apps that Oscar depends on
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'django_tables2',
    'compressor',
    'rest_framework',
    'celery',
    'django_celery_beat',
    'django_celery_results',

    # Django apps that the sandbox depends on
    'django.contrib.sitemaps',

    # 3rd-party apps that the sandbox depends on
    # 'django_extensions',
]
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

# =============
# AUTHENTICATION
# =============

PHONE_BACKEND = "apps.user.auth_backends.PhoneBackend"

AUTHENTICATION_BACKENDS = (
    'apps.user.auth_backends.PhoneBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]

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
