from django.urls import path
from core.application import Config
from core.loading import get_class


class StoreConfig(Config):
    label = "store"
    name = "apps.webshop.store"
    verbose_name = "Магазин"

    namespace = "store"

    # pylint: disable=unused-import
    def ready(self):
        from . import receivers

        self.store_select = get_class("webshop.store.views", "StoreSelectModalView")

    def get_urls(self):
        urls = [
            path("api/select/", self.store_select.as_view(), name="select"),
        ]

        return self.post_process_urls(urls)
