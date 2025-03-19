from core.application import Config
from django.contrib.auth.decorators import login_required
from django.urls import path
from core.loading import get_class


class OrderReviewsConfig(Config):
    label = "order_reviews"
    name = "apps.webshop.order.reviews"
    module = "apps.webshop.order"

    verbose_name = "Отзывы на заказы"

    # pylint: disable=attribute-defined-outside-init, reimported, unused-import
    def ready(self):
        self.reviews_available_view = get_class(
            "webshop.order.reviews.views", "OrderFeedbackAvailibleListView"
        )
        self.reviews_view = get_class(
            "webshop.order.reviews.views", "OrderFeedbackListView"
        )
        self.reviews_add_view = get_class(
            "webshop.order.reviews.views", "AddOrderFeedbackView"
        )

    def get_urls(self):
        urls = [
            path(
                "",
                login_required(self.reviews_view.as_view()),
                name="reviews",
            ),
            path(
                "available/",
                login_required(self.reviews_available_view.as_view()),
                name="reviews-available",
            ),
            path(
                "add/",
                login_required(self.reviews_add_view.as_view()),
                name="reviews-add",
            ),
        ]

        return self.post_process_urls(urls)
