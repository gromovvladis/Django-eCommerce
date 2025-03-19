from django.urls import re_path
from core.application import Config
from core.loading import get_class


class OfferConfig(Config):
    label = "offer"
    name = "apps.webshop.offer"
    verbose_name = "Акции"

    namespace = "offer"

    # pylint: disable=attribute-defined-outside-init, W0611, W0201
    def ready(self):
        from . import receivers

        self.detail_view = get_class("webshop.offer.views", "OfferDetailView")
        self.upsell_view = get_class("webshop.offer.views", "GetUpsellMasseges")

    def get_urls(self):
        urls = [
            re_path(r"^(?P<slug>[\w-]+)/$", self.detail_view.as_view(), name="detail"),
            re_path(
                r"^(?P<slug>[\w-]+)/upsell/$", self.upsell_view.as_view(), name="upsell"
            ),
        ]
        return self.post_process_urls(urls)
