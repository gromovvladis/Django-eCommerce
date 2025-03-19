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
    "apps.webshop.order.reviews.apps.OrderReviewsConfig"
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
    "compressor",  # static
    "rest_framework",  # api
    "celery",  # celery
    "django_celery_beat",
    "django_celery_results",
    "django_tables2",  # tables
    "django.contrib.sitemaps",  # sitemap
]


default_app_config = "apps.webshop.apps.WebshopConfig"
