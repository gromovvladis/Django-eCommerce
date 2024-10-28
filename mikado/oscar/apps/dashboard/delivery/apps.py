from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class DeliveryDashboardConfig(OscarDashboardConfig):
    label = "delivery_dashboard"
    name = "oscar.apps.dashboard.delivery"
    verbose_name = "Панель управления - Доставка"

    default_permissions = [
        "user.full_access",
        "delivery.full_access",
    ]

    permissions_map = {
        "delivery-active": (["user.full_access"], ["delivery.full_access"], ["delivery.read"]),
        "delivery-list": (["user.full_access"], ["delivery.full_access"], ["delivery.read"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.delivery_active_view = get_class("dashboard.delivery.views", "DeliveryActiveView")
        self.delivery_list_view = get_class("dashboard.delivery.views", "DeliveryListView")

        self.delivery_partner_view = get_class("dashboard.delivery.views", "DeliveryPartnerView")
        self.delivery_couriers_view = get_class("dashboard.delivery.views", "DeliveryCouriersView")

        self.delivery_stats_view = get_class("dashboard.delivery.views", "DeliveryStatsView")

        self.delivery_json_view = get_class("dashboard.delivery.views", "DeliveryZonesGeoJsonView")
        self.delivery_zona_view = get_class("dashboard.delivery.views", "DeliveryZonaView")
        self.delivery_zones_view = get_class("dashboard.delivery.views", "DeliveryZonesView")
        self.delivery_zones_create_view = get_class("dashboard.delivery.views", "DeliveryZonesCreateView")
        self.delivery_zones_update_view = get_class("dashboard.delivery.views", "DeliveryZonesUpdateView")
        self.delivery_zones_delete_view = get_class("dashboard.delivery.views", "DeliveryZonesDeleteView")
        self.delivery_zones_hide_view = get_class("dashboard.delivery.views", "DeliveryZonesHideView")
        self.delivery_zones_available_view = get_class("dashboard.delivery.views", "DeliveryZonesAvailableView")
                
        self.delivery_couriers_list_view = get_class("dashboard.delivery.views", "DeliveryCouriersListView")
        self.delivery_couriers_detail_view = get_class("dashboard.delivery.views", "DeliveryCouriersDetailView")

    def get_urls(self):
        urls = [
            
            path("active/", self.delivery_active_view.as_view(), name="delivery-active"),
            path("all/", self.delivery_list_view.as_view(), name="delivery-list"),

            path("orders-partner/", self.delivery_partner_view.as_view(), name="delivery-partners"),
            path("orders-courier/", self.delivery_couriers_view.as_view(), name="delivery-couriers"),
            
            path("statistic/", self.delivery_stats_view.as_view(), name="delivery-stats"),
            
            path("api/zona/", self.delivery_json_view.as_view(), name="delivery-zona-json"),
            path("zona/", self.delivery_zona_view.as_view(), name="delivery-zona"),
            path("zones/", self.delivery_zones_view.as_view(), name="delivery-zones"),
            path("zones/create/", self.delivery_zones_create_view.as_view(), name="delivery-create-zona"),
            path("zones/<int:pk>/update/", self.delivery_zones_update_view.as_view(), name="delivery-update-zona"),
            path("zones/<int:pk>/delete/", self.delivery_zones_delete_view.as_view(), name="delivery-delete-zona"),
            path("zones/<int:pk>/hide/", self.delivery_zones_hide_view.as_view(), name="delivery-hide-zona"),
            path("zones/<int:pk>/available/", self.delivery_zones_available_view.as_view(), name="delivery-available-zona"),

            path("couriers/", self.delivery_couriers_list_view.as_view(), name="delivery-couriers-list"),
            path("couriers/<int:pk>/", self.delivery_couriers_detail_view.as_view(), name="delivery-couriers-detail"),

        ]
        return self.post_process_urls(urls)
