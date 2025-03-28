from core.application import Config
from core.loading import get_class
from django.urls import path


class ShippingConfig(Config):
    label = "shipping"
    name = "apps.webshop.shipping"
    verbose_name = "Доставка"

    namespace = "shipping"

    # pylint: disable=attribute-defined-outside-init, W0611, W0201
    def ready(self):
        self.order_now_view = get_class("webshop.shipping.views", "OrderNowView")
        self.order_later_view = get_class("webshop.shipping.views", "OrderLaterView")
        self.shipping_zones_view = get_class(
            "webshop.shipping.views", "ShippingZonesGeoJsonView"
        )

    def get_urls(self):
        urls = [
            path("api/order-now/", self.order_now_view.as_view(), name="order-now"),
            path(
                "api/order-later/", self.order_later_view.as_view(), name="order-later"
            ),
            path(
                "api/shipping-zones/",
                self.shipping_zones_view.as_view(),
                name="shipping-zones",
            ),
        ]
        return self.post_process_urls(urls)
