from oscar.core.application import OscarConfig
from oscar.core.loading import get_class
from django.urls import path


class OrderConfig(OscarConfig):
    label = "order"
    name = "oscar.apps.order"
    verbose_name = "Заказ"

    # def ready(self):
    #         self.callback_komtet = get_class("order.views", "CallbackKomtet")

    # def get_urls(self):
    #     urls = [
    #         path("callback/", self.callback_komtet.as_view(), name="callback"),
    #     ]
    #     return self.post_process_urls(urls)
