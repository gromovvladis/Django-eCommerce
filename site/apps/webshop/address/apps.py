from django.urls import path
from core.application import Config
from core.loading import get_class


class AddressConfig(Config):
    label = "address"
    name = "apps.webshop.address"
    verbose_name = "Адрес"

    namespace = "address"

    # pylint: disable=attribute-defined-outside-init, W0611, W0201
    def ready(self):
        self.set_address_view = get_class("webshop.address.views", "SetAddressView")
        self.pickup_address_view = get_class("webshop.address.views", "PickUpView")

    def get_urls(self):
        urls = [
            path(
                "shipping-address/",
                self.set_address_view.as_view(),
                name="shipping-address",
            ),
            path(
                "pickup-address/",
                self.pickup_address_view.as_view(),
                name="pickup-address",
            ),
        ]
        return self.post_process_urls(urls)
