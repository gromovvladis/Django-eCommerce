from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class DeliveryDashboardConfig(OscarDashboardConfig):
    label = "delivery_dashboard"
    name = "oscar.apps.dashboard.delivery"
    verbose_name = "Панель управления - Доставка"

    default_permissions = [
        "is_staff",
    ]
    permissions_map = {
        "delivery-stats": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-map": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-couriers-list": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-kitchen": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-couriers": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.delivery_stats_view = get_class("dashboard.delivery.views", "DeliveryStatsView")
        self.delivery_map_view = get_class("dashboard.delivery.views", "DeliveryMapView")
        self.delivery_couriers_list_view = get_class("dashboard.delivery.views", "DeliveryCouriersListView")
        self.delivery_kitchen_view = get_class("dashboard.delivery.views", "DeliveryKitchenView")
        self.delivery_couriers_view = get_class("dashboard.delivery.views", "DeliveryCouriersView")

    def get_urls(self):
        urls = [
            path("", self.delivery_stats_view.as_view(), name="delivery-stats"),
            path("map/", self.delivery_map_view.as_view(), name="delivery-map"),
            path("couriers-list/", self.delivery_couriers_list_view.as_view(), name="delivery-couriers-list"),
            path("kitchen/", self.delivery_kitchen_view.as_view(), name="delivery-kitchen"),
            path("couriers/", self.delivery_couriers_view.as_view(), name="delivery-couriers"),
        ]
        return self.post_process_urls(urls)
