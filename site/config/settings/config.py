from django.apps import apps
from django.urls import path

from oscar.core.application import OscarConfig


class Shop(OscarConfig):
    name = "oscar"

    def ready(self):
        self.page_app = apps.get_app_config("page")
        self.catalogue_app = apps.get_app_config("catalogue")
        self.basket_app = apps.get_app_config("basket")
        self.checkout_app = apps.get_app_config("checkout")
        self.action_app = apps.get_app_config("action")
        self.customer_app = apps.get_app_config("customer")
        self.search_app = apps.get_app_config("search")
        self.offer_app = apps.get_app_config("offer")
        self.wishlists_app = apps.get_app_config("wishlists")
        self.shipping_app = apps.get_app_config("shipping")
        self.address_app = apps.get_app_config("address")
        self.payment_app = apps.get_app_config("payment")
        self.store_app = apps.get_app_config("store")
        self.delivery_app = apps.get_app_config("delivery")
        self.telegram_app = apps.get_app_config("telegram")
        self.evotor_app = apps.get_app_config("evotor")
        self.communication_app = apps.get_app_config("communication")
        self.sms_app = apps.get_app_config("sms")
        self.dashboard_app = apps.get_app_config("dashboard")

    def get_urls(self):
        urls = [
            path("", self.page_app.urls),
            path("menu/", self.catalogue_app.urls),
            path("cart/", self.basket_app.urls),
            path("checkout/", self.checkout_app.urls),
            path("actions/", self.action_app.urls),
            path("accounts/", self.customer_app.urls),
            path("search/", self.search_app.urls),
            path("offers/", self.offer_app.urls),
            path("wishlists/", self.wishlists_app.urls),
            path("shipping/", self.shipping_app.urls),
            path("address/", self.address_app.urls),
            path("payment/", self.payment_app.urls),
            path("store/", self.store_app.urls),
            path("delivery/", self.delivery_app.urls),
            path("telegram/", self.telegram_app.urls),
            path("evotor/", self.evotor_app.urls),
            path("communication/", self.communication_app.urls),
            path("dashboard/", self.dashboard_app.urls),
        ]
        return urls
