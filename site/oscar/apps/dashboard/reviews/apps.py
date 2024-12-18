from django.urls import path
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class ReviewsDashboardConfig(OscarDashboardConfig):
    label = "reviews_dashboard"
    name = "oscar.apps.dashboard.reviews"
    verbose_name = "Панель управления - Отзывы"

    default_permissions = [
        "user.full_access",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.product_list_view = get_class("dashboard.reviews.views", "ReviewProductListView")
        self.order_list_view = get_class("dashboard.reviews.views", "ReviewOrderListView")
        self.update_view = get_class("dashboard.reviews.views", "ReviewUpdateView")
        self.delete_view = get_class("dashboard.reviews.views", "ReviewDeleteView")

    def get_urls(self):
        urls = [
            path("", self.product_list_view.as_view(), name="reviews-product-list"),
            path("", self.order_list_view.as_view(), name="reviews-order-list"),
            path("<int:pk>/", self.update_view.as_view(), name="reviews-update"),
            path("<int:pk>/delete/", self.delete_view.as_view(), name="reviews-delete"),
        ]
        return self.post_process_urls(urls)
