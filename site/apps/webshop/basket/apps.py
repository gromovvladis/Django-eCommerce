# pylint: disable=W0201
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from core.application import Config
from core.loading import get_class


class BasketConfig(Config):
    label = "basket"
    name = "apps.webshop.basket"
    verbose_name = "Корзина"

    namespace = "basket"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.summary_view = get_class("webshop.basket.views", "BasketView")
        self.add_view = get_class("webshop.basket.views", "BasketAddView")
        self.empty_view = get_class("webshop.basket.views", "EmptyBasketView")
        self.upsell_view = get_class("webshop.basket.views", "GetUpsellMasseges")

    def get_urls(self):
        urls = [
            path("", self.summary_view.as_view(), name="summary"),
            path("add/<str:slug>/", self.add_view.as_view(), name="add"),
            path("empty/", csrf_exempt(self.empty_view.as_view()), name="empty"),
            path("upsell/", self.upsell_view.as_view(), name="upsell"),
        ]
        return self.post_process_urls(urls)
