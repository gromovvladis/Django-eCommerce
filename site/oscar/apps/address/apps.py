from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class

class AddressConfig(OscarConfig):
    label = "address"
    name = "oscar.apps.address"
    verbose_name = "Адрес"

    namespace = "address"

    # pylint: disable=attribute-defined-outside-init, W0611, W0201
    def ready(self):
        self.set_address_view = get_class("address.views", "SetAddressView")
        self.pickup_address_view = get_class("address.views", "PickUpView")
        # self.session_address_view = get_class("address.views", "SessionAddressView")

    def get_urls(self):
        urls = [
            path("delivery-address/", self.set_address_view.as_view(), name="delivery-address"),
            path("pickup-address/", self.pickup_address_view.as_view(), name="pickup-address"),
            # path("api/session-address/", self.session_address_view.as_view(), name="session-address"),
        ]
        return self.post_process_urls(urls)
