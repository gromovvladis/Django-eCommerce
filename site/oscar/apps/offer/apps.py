from django.urls import path, re_path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class OfferConfig(OscarConfig):
    label = "offer"
    name = "oscar.apps.offer"
    verbose_name = "Предложения"

    namespace = "offer"

    # pylint: disable=attribute-defined-outside-init, W0611, W0201
    def ready(self):
        from . import receivers

        self.detail_view = get_class("offer.views", "OfferDetailView")
        self.upsell_view = get_class("offer.views", "GetUpsellMasseges")

    def get_urls(self):
        urls = [
            re_path(r"^(?P<slug>[\w-]+)/$", self.detail_view.as_view(), name="detail"),
            re_path(
                r"^(?P<slug>[\w-]+)/upsell/$", self.upsell_view.as_view(), name="upsell"
            ),
        ]
        return self.post_process_urls(urls)
