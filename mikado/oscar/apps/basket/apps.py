# pylint: disable=W0201
from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class
from django.views.decorators.csrf import csrf_exempt


class BasketConfig(OscarConfig):
    label = "basket"
    name = "oscar.apps.basket"
    verbose_name = "Корзина"

    namespace = "basket"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.summary_view = get_class("basket.views", "BasketView")
        self.add_view = get_class("basket.views", "BasketAddView")
        self.empty_view = get_class("basket.views", "EmptyBasketView")
        self.upsell_view = get_class("basket.views", "GetUpsellMasseges")
        self.saved_view = get_class("basket.views", "SavedView")

    def get_urls(self):
        urls = [
            path("", self.summary_view.as_view(), name="summary"),
            path("add/<str:slug>/", self.add_view.as_view(), name="add"),
            path("empty/", csrf_exempt(self.empty_view.as_view()), name="empty"),
            path("upsell/", self.upsell_view.as_view(), name="upsell"),
            path("saved/", self.saved_view.as_view(), name="saved"),
        ]
        return self.post_process_urls(urls)
