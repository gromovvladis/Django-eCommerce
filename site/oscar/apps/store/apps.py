from oscar.core.application import OscarConfig
from django.urls import path
from oscar.core.loading import get_class


class StoreConfig(OscarConfig):
    label = "store"
    name = "oscar.apps.store"
    verbose_name = "Магазин"

    namespace = "store"

    # pylint: disable=unused-import
    def ready(self):
        from . import receivers

        self.store_select = get_class("store.views", "StoreSelectModalView")

    def get_urls(self):
        urls = [
            path("api/select/", self.store_select.as_view(), name="select"),
        ]

        return self.post_process_urls(urls)