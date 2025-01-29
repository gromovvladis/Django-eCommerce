from django.contrib.auth.decorators import login_required
from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CatalogueReviewsConfig(OscarConfig):
    label = "reviews"
    name = "oscar.apps.catalogue.reviews"
    verbose_name = "Отзывы на товары"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.review_create_view = get_class("catalogue.reviews.views", "CreateProductReview")
        self.review_list_view = get_class("catalogue.reviews.views", "ProductReviewList")

    def get_urls(self):
        urlpatterns = [
            path("add/", login_required(self.review_create_view.as_view()), name="reviews-add"),
            path("", login_required(self.review_list_view.as_view()), name="reviews-list"),
        ]
        return self.post_process_urls(urlpatterns)
