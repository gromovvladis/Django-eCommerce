from django.apps import apps
from django.urls import path

from oscar.core.application import OscarConfig

class Shop(OscarConfig):
    name = "oscar"

    def ready(self):

        self.home_app = apps.get_app_config("home")
        self.catalogue_app = apps.get_app_config("catalogue")
        self.customer_app = apps.get_app_config("customer")
        self.basket_app = apps.get_app_config("basket")
        self.checkout_app = apps.get_app_config("checkout")
        self.search_app = apps.get_app_config("search")
        self.dashboard_app = apps.get_app_config("dashboard")
        self.offer_app = apps.get_app_config("offer")
        self.wishlists_app = apps.get_app_config("wishlists")
        self.sms_auth_app = apps.get_app_config("sms_auth")
        self.shipping_app = apps.get_app_config("shipping")
        self.address_app = apps.get_app_config("address")
        self.payment_app = apps.get_app_config("payment")
        self.store_app = apps.get_app_config("store")
        self.delivery_app = apps.get_app_config("delivery")
        self.telegram_app = apps.get_app_config("telegram")
        self.crm_app = apps.get_app_config("crm")

    def get_urls(self):
        urls = [
            path("", self.home_app.urls, name="home"),
            path("menu/", self.catalogue_app.urls),
            path("cart/", self.basket_app.urls),
            path("checkout/", self.checkout_app.urls),
            path("accounts/", self.customer_app.urls),
            path("search/", self.search_app.urls),
            path("dashboard/", self.dashboard_app.urls),
            path("offers/", self.offer_app.urls),
            path("wishlists/", self.wishlists_app.urls),
            path("shipping/", self.shipping_app.urls),
            path("address/", self.address_app.urls),
            path("payment/", self.payment_app.urls),
            path("store/", self.store_app.urls),
            path("delivery/", self.delivery_app.urls),
            path("telegram/", self.telegram_app.urls),
            path("crm/", self.crm_app.urls),
        ]
        return urls
