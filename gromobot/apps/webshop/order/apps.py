from core.application import Config
from django.apps import apps
from django.urls import include, re_path


class OrderOnlyConfig(Config):
    label = "order"
    name = "apps.webshop.order"
    verbose_name = "Заказ"

    namespace = "order"


class OrderReviewsOnlyConfig(Config):
    label = "order"
    name = "apps.webshop.order.reviews"
    verbose_name = "Отзывы на заказы"

    # pylint: disable=attribute-defined-outside-init, unused-import
    def ready(self):
        from . import receivers

        super().ready()

        self.reviews_app = apps.get_app_config("order_reviews")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            re_path(
                r"^(?P<order_number>\d+)/reviews/",
                include(self.reviews_app.urls[0]),
            ),
        ]
        return self.post_process_urls(urls)


class OrderConfig(OrderOnlyConfig, OrderReviewsOnlyConfig):
    """
    Composite class combining Orders with Reviews
    """


# from core.application import Config

# # from core.loading import get_class
# # from django.urls import path


# class OrderConfig(Config):
#     label = "order"
#     name = "apps.webshop.order"
#     verbose_name = "Заказ"

#     # def ready(self):
#     #         self.callback_komtet = get_class("webshop.order.views", "CallbackKomtet")

#     # def get_urls(self):
#     #     urls = [
#     #         path("callback/", self.callback_komtet.as_view(), name="callback"),
#     #     ]
#     #     return self.post_process_urls(urls)
