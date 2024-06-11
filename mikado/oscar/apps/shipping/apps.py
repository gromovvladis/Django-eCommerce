
from django.urls import path
from oscar.core.loading import get_class
from oscar.core.application import OscarConfig


class ShippingConfig(OscarConfig):
    label = "shipping"
    name = "oscar.apps.shipping"
    verbose_name = "Доставка"

    namespace = "shipping"

    # pylint: disable=attribute-defined-outside-init, W0611, W0201
    def ready(self):
        self.delivery_time_view = get_class("shipping.views", "DelievryTimeView")
        self.pickup_time_view = get_class("shipping.views", "PickUpTimeView")
        self.delivery_zones_view = get_class("shipping.views", "DeliveryZonesView")
        self.delivery_later_view = get_class("shipping.views", "DeliveryLaterView")

    def get_urls(self):
        urls = [
            path("api/delivery-time/", self.delivery_time_view.as_view(), name="delivery-time"),
            path("api/pickup-time/", self.pickup_time_view.as_view(), name="pickup-time"),
            path("api/delivery-zones/", self.delivery_zones_view.as_view(), name="delivery-zones"),
            path("api/delivery-later/", self.delivery_later_view.as_view(), name="delivery-later"),
        ]
        return self.post_process_urls(urls)


