from .run_celery import app as celery_app

__all__ = ("celery_app",)

# Use 'alpha', 'beta', 'rc' or 'final' as the 4th element to indicate release type.
VERSION = (3, 2, 4, "final")


def get_short_version():
    return "%s.%s" % (VERSION[0], VERSION[1])


def get_version():
    version = "%s.%s" % (VERSION[0], VERSION[1])
    # Append 3rd digit if > 0
    if VERSION[2]:
        version = "%s.%s" % (version, VERSION[2])

    if VERSION[3] != "final":
        mapping = {"alpha": "a", "beta": "b", "rc": "rc"}
        version = "%s%s" % (version, mapping[VERSION[3]])
        if len(VERSION) == 5:
            version = "%s%s" % (version, VERSION[4])

    return version


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",
    "config.settings.config.Shop",
    "oscar.apps.page.apps.PageConfig",
    "oscar.apps.action.apps.ActionConfig",
    "oscar.apps.analytics.apps.AnalyticsConfig",
    "oscar.apps.checkout.apps.CheckoutConfig",
    "oscar.apps.address.apps.AddressConfig",
    "oscar.apps.shipping.apps.ShippingConfig",
    "oscar.apps.delivery.apps.DeliveryConfig",
    "oscar.apps.catalogue.apps.CatalogueConfig",
    "oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig",
    "oscar.apps.communication.apps.CommunicationConfig",
    "oscar.apps.store.apps.StoreConfig",
    "oscar.apps.basket.apps.BasketConfig",
    "oscar.apps.payment.apps.PaymentConfig",
    "oscar.apps.offer.apps.OfferConfig",
    "oscar.apps.order.apps.OrderConfig",
    "oscar.apps.customer.apps.CustomerConfig",
    "oscar.apps.search.apps.SearchConfig",
    "oscar.apps.voucher.apps.VoucherConfig",
    "oscar.apps.wishlists.apps.WishlistsConfig",
    "oscar.apps.telegram.apps.TelegramConfig",
    "oscar.apps.evotor.apps.EvotorConfig",
    "oscar.apps.user.apps.UserConfig",
    "oscar.apps.settings.apps.SettingsConfig",
    "oscar.apps.sms.apps.SmsConfig",
    "oscar.apps.dashboard.apps.DashboardConfig",
    "oscar.apps.dashboard.reports.apps.ReportsDashboardConfig",
    "oscar.apps.dashboard.users.apps.UsersDashboardConfig",
    "oscar.apps.dashboard.orders.apps.OrdersDashboardConfig",
    "oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig",
    "oscar.apps.dashboard.offers.apps.OffersDashboardConfig",
    "oscar.apps.dashboard.stores.apps.StoresDashboardConfig",
    "oscar.apps.dashboard.pages.apps.PagesDashboardConfig",
    "oscar.apps.dashboard.ranges.apps.RangesDashboardConfig",
    "oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig",
    "oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig",
    "oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig",
    "oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig",
    "oscar.apps.dashboard.payments.apps.PaymentsDashboardConfig",
    "oscar.apps.dashboard.evotor.apps.EvotorDashboardConfig",
    "oscar.apps.dashboard.delivery.apps.DeliveryDashboardConfig",
    "oscar.apps.dashboard.telegram.apps.TelegramDashboardConfig",
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


default_app_config = "config.settings.config.Shop"
