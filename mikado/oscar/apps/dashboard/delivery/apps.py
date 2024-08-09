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
        "delivery-now": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-zones": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-couriers-list": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-kitchen": (["is_staff"], ["partner.dashboard_access"]),
        "delivery-couriers": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.delivery_stats_view = get_class("dashboard.delivery.views", "DeliveryStatsView")
        self.delivery_now_view = get_class("dashboard.delivery.views", "DeliveryNowView")
        self.delivery_zona_view = get_class("dashboard.delivery.views", "DeliveryZonaView")
        self.delivery_zones_view = get_class("dashboard.delivery.views", "DeliveryZonesView")
        self.delivery_zones_create_view = get_class("dashboard.delivery.views", "DeliveryZonesCreateView")
        self.delivery_zones_update_view = get_class("dashboard.delivery.views", "DeliveryZonesUpdateView")
        self.delivery_zones_delete_view = get_class("dashboard.delivery.views", "DeliveryZonesDeleteView")
        
        self.delivery_zones_hide_view = get_class("dashboard.delivery.views", "DeliveryZonesHideView")
        self.delivery_zones_available_view = get_class("dashboard.delivery.views", "DeliveryZonesAvailableView")

        self.delivery_couriers_list_view = get_class("dashboard.delivery.views", "DeliveryCouriersListView")
        self.delivery_kitchen_view = get_class("dashboard.delivery.views", "DeliveryKitchenView")
        self.delivery_couriers_view = get_class("dashboard.delivery.views", "DeliveryCouriersView")

    def get_urls(self):
        urls = [
            path("", self.delivery_stats_view.as_view(), name="delivery-stats"),
            path("map/", self.delivery_now_view.as_view(), name="delivery-now"),
            path("zona/", self.delivery_zona_view.as_view(), name="delivery-zona"),
            path("zones/", self.delivery_zones_view.as_view(), name="delivery-zones"),
            path("zones/create/", self.delivery_zones_create_view.as_view(), name="delivery-create-zona"),
            path("zones/<int:pk>/update/", self.delivery_zones_update_view.as_view(), name="delivery-update-zona"),
            path("zones/<int:pk>/delete/", self.delivery_zones_delete_view.as_view(), name="delivery-delete-zona"),
            
            path("zones/<int:pk>/hide/", self.delivery_zones_hide_view.as_view(), name="delivery-hide-zona"),
            path("zones/<int:pk>/available/", self.delivery_zones_available_view.as_view(), name="delivery-available-zona"),

            path("couriers-list/", self.delivery_couriers_list_view.as_view(), name="delivery-couriers-list"),
            path("kitchen/", self.delivery_kitchen_view.as_view(), name="delivery-kitchen"),
            path("couriers/", self.delivery_couriers_view.as_view(), name="delivery-couriers"),
        ]
        return self.post_process_urls(urls)
