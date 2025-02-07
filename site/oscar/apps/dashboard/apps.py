from django.apps import apps
from django.urls import include, path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class DashboardConfig(OscarDashboardConfig):
    label = "dashboard"
    name = "oscar.apps.dashboard"
    verbose_name = "Панель управления"

    namespace = "dashboard"
    permissions_map = {
        "index": (["is_staff"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.index_view = get_class("dashboard.views", "IndexView")
        self.navbarcash_view = get_class("dashboard.views", "NavbarCash")
        self.login_view = get_class("dashboard.views", "LoginView")

        self.catalogue_app = apps.get_app_config("catalogue_dashboard")
        self.reports_app = apps.get_app_config("reports_dashboard")
        self.orders_app = apps.get_app_config("orders_dashboard")
        self.users_app = apps.get_app_config("users_dashboard")
        self.pages_app = apps.get_app_config("pages_dashboard")
        self.stores_app = apps.get_app_config("stores_dashboard")
        self.offers_app = apps.get_app_config("offers_dashboard")
        self.ranges_app = apps.get_app_config("ranges_dashboard")
        self.reviews_app = apps.get_app_config("reviews_dashboard")
        self.vouchers_app = apps.get_app_config("vouchers_dashboard")
        self.comms_app = apps.get_app_config("communications_dashboard")
        self.shipping_app = apps.get_app_config("shipping_dashboard")
        self.payments_app = apps.get_app_config("payments_dashboard")
        self.delivery_app = apps.get_app_config("delivery_dashboard")
        self.telegram_app = apps.get_app_config("telegram_dashboard")
        self.crm_app = apps.get_app_config("crm_dashboard")

    def get_urls(self):
        from django.contrib.auth import views as auth_views

        urls = [
            path("", self.index_view.as_view(), name="index"),
            path("navbar-cash/", self.navbarcash_view.as_view(), name="navbar-cash"),
            path("catalogue/", include(self.catalogue_app.urls[0])),
            path("reports/", include(self.reports_app.urls[0])),
            path("orders/", include(self.orders_app.urls[0])),
            path("users/", include(self.users_app.urls[0])),
            path("pages/", include(self.pages_app.urls[0])),
            path("stores/", include(self.stores_app.urls[0])),
            path("offers/", include(self.offers_app.urls[0])),
            path("ranges/", include(self.ranges_app.urls[0])),
            path("reviews/", include(self.reviews_app.urls[0])),
            path("vouchers/", include(self.vouchers_app.urls[0])),
            path("comms/", include(self.comms_app.urls[0])),
            path("shipping/", include(self.shipping_app.urls[0])),
            path("payments/", include(self.payments_app.urls[0])),
            path("delivery/", include(self.delivery_app.urls[0])),
            path("telegram/", include(self.telegram_app.urls[0])),
            path("crm/", include(self.crm_app.urls[0])),
            path("login/", self.login_view.as_view(), name="login"),
            path(
                "logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"
            ),
        ]
        return self.post_process_urls(urls)
