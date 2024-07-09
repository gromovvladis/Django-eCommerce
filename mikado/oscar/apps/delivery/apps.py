from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class

class DeliveryConfig(OscarConfig):
    label = "delivery"
    name = "oscar.apps.delivery"
    verbose_name = "Доставка"

    namespace = "delivery"

    # pylint: disable=attribute-defined-outside-init, W0611, W0201
    def ready(self):
        self.delivery_now_view = get_class("delivery.views", "DeliveryNowView")
        self.delivery_later_view = get_class("delivery.views", "DeliveryLaterView")
        self.delivery_zones_view = get_class("delivery.views", "DeliveryZonesGeoJsonView")

    def get_urls(self):
        urls = [
            path("api/delivery-now/", self.delivery_now_view.as_view(), name="delivery-now"),
            path("api/delivery-later/", self.delivery_later_view.as_view(), name="delivery-later"),
            path("api/delivery-zones/", self.delivery_zones_view.as_view(), name="delivery-zones"),
        ]
        return self.post_process_urls(urls)
