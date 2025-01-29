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

        self.product_update_view = get_class("dashboard.reviews.views", "ReviewProductUpdateView")
        self.product_read_view = get_class("dashboard.reviews.views", "ReviewProductReadView")
        self.product_delete_view = get_class("dashboard.reviews.views", "ReviewProductDeleteView")
        
        self.order_update_view = get_class("dashboard.reviews.views", "ReviewOrderUpdateView")
        self.order_read_view = get_class("dashboard.reviews.views", "ReviewOrderReadView")
        self.order_delete_view = get_class("dashboard.reviews.views", "ReviewOrderDeleteView")

    def get_urls(self):
        urls = [
            path("products/", self.product_list_view.as_view(), name="reviews-product-list"),
            path("products/<int:pk>/", self.product_update_view.as_view(), name="reviews-product-update"),
            path("products/<int:pk>/read/", self.product_read_view.as_view(), name="reviews-product-read"),
            path("products/<int:pk>/delete/", self.product_delete_view.as_view(), name="reviews-product-delete"),

            path("orders/", self.order_list_view.as_view(), name="reviews-order-list"),
            path("orders/<int:pk>/", self.order_update_view.as_view(), name="reviews-order-update"),
            path("orders/<int:pk>/read/", self.order_read_view.as_view(), name="reviews-order-read"),
            path("orders/<int:pk>/delete/", self.order_delete_view.as_view(), name="reviews-order-delete"),
        ]
        return self.post_process_urls(urls)
