from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class OrdersDashboardConfig(OscarDashboardConfig):
    label = "orders_dashboard"
    name = "oscar.apps.dashboard.orders"
    verbose_name = "Панель управления - Заказы"

    default_permissions = [
        "is_staff",
    ]
    permissions_map = {
        "order-list": (["is_staff"], ["partner.dashboard_access"]),
        "order-stats": (["is_staff"], ["partner.dashboard_access"]),
        "order-detail": (["is_staff"], ["partner.dashboard_access"]),
        "order-detail-note": (["is_staff"], ["partner.dashboard_access"]),
        "order-line-detail": (["is_staff"], ["partner.dashboard_access"]),
        "order-shipping-address": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.order_list_view = get_class("dashboard.orders.views", "OrderListView")
        self.order_detail_view = get_class("dashboard.orders.views", "OrderDetailView")
        self.shipping_address_view = get_class(
            "dashboard.orders.views", "ShippingAddressUpdateView"
        )
        self.line_detail_view = get_class("dashboard.orders.views", "LineDetailView")
        self.order_stats_view = get_class("dashboard.orders.views", "OrderStatsView")
        #vlad
        self.update_sorce_view = get_class("dashboard.orders.views", "UpdateSourceView")
        self.delete_source_view = get_class("dashboard.orders.views", "DeleteSourceView")
        self.refund_transaction_view = get_class("dashboard.orders.views", "RefundTransactionView")
        self.add_source_view = get_class("dashboard.orders.views", "AddSourceView")
        self.add_transaction_view = get_class("dashboard.orders.views", "AddTransactionView")

    def get_urls(self):
        urls = [
            path("", self.order_list_view.as_view(), name="order-list"),
            path("statistics/", self.order_stats_view.as_view(), name="order-stats"),
            path(
                "<str:number>/", self.order_detail_view.as_view(), name="order-detail"
            ),
            path(
                "<str:number>/notes/<int:note_id>/",
                self.order_detail_view.as_view(),
                name="order-detail-note",
            ),
            path(
                "<str:number>/lines/<int:line_id>/",
                self.line_detail_view.as_view(),
                name="order-line-detail",
            ),
            path(
                "<str:number>/shipping-address/",
                self.shipping_address_view.as_view(),
                name="order-shipping-address",
            ),
            #vlad
            path(
                "<str:number>/update-source/<int:pk>",
                self.update_sorce_view.as_view(), 
                name='update-source'
            ),
            path(
                "<str:number>/delete-source/<int:pk>",
                self.delete_source_view.as_view(), 
                name='delete-source'
            ),
            path(
                "<str:number>/add-source/",
                self.add_source_view.as_view(), 
                name='add-source'
            ),
            path(
                "<str:number>/add-transaction/",
                self.add_transaction_view.as_view(), 
                name='add-transaction'
            ),
            path(
                "<str:number>/refund-transaction/<str:pk>",
                self.refund_transaction_view.as_view(), 
                name='refund-transaction'
            ),
        ]
        return self.post_process_urls(urls)
