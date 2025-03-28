from core.application import Config
from core.loading import get_class
from django.contrib.auth.decorators import login_required
from django.urls import path


class CatalogueReviewsConfig(Config):
    label = "product_reviews"
    name = "apps.webshop.catalogue.reviews"
    module = "apps.webshop.catalogue"

    verbose_name = "Отзывы на товары"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.review_create_view = get_class(
            "webshop.catalogue.reviews.views", "CreateProductReview"
        )
        self.review_list_view = get_class(
            "webshop.catalogue.reviews.views", "ProductReviewList"
        )

    def get_urls(self):
        urlpatterns = [
            path(
                "add/",
                login_required(self.review_create_view.as_view()),
                name="reviews-add",
            ),
            path(
                "", login_required(self.review_list_view.as_view()), name="reviews-list"
            ),
        ]
        return self.post_process_urls(urlpatterns)
