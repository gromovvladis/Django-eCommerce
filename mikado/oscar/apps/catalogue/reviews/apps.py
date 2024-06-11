from django.contrib.auth.decorators import login_required
from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CatalogueReviewsConfig(OscarConfig):
    label = "reviews"
    name = "oscar.apps.catalogue.reviews"
    verbose_name = "Отзывы на товары"

    hidable_feature_name = "reviews"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        # self.detail_view = get_class("catalogue.reviews.views", "ProductReviewDetail")
        self.create_view = get_class("catalogue.reviews.views", "CreateProductReview")
        self.list_view = get_class("catalogue.reviews.views", "ProductReviewList")

    def get_urls(self):
        urls = [
            # path("", login_required(self.detail_view.as_view()), name="my-reviews"),
            path("add/", login_required(self.create_view.as_view()), name="reviews-add"),
            path("", login_required(self.list_view.as_view()), name="reviews-list"),
        ]
        return self.post_process_urls(urls)
