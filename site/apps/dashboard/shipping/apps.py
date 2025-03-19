from django.urls import path
from core.application import DashboardConfig
from core.loading import get_class


class ShippingDashboardConfig(DashboardConfig):
    label = "shipping_dashboard"
    name = "apps.dashboard.shipping"
    verbose_name = "Панель управления - Доставка"

    default_permissions = [
        "user.full_access",
        "shipping.full_access",
    ]

    permissions_map = {
        "shipping-active": (
            ["user.full_access"],
            ["shipping.full_access"],
            ["shipping.read"],
        ),
        "shipping-list": (
            ["user.full_access"],
            ["shipping.full_access"],
            ["shipping.read"],
        ),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.shipping_active_view = get_class(
            "dashboard.shipping.views", "ShippingActiveView"
        )
        self.shipping_list_view = get_class(
            "dashboard.shipping.views", "ShippingListView"
        )

        self.shipping_store_view = get_class(
            "dashboard.shipping.views", "ShippingStoreView"
        )
        self.shipping_couriers_view = get_class(
            "dashboard.shipping.views", "ShippingCouriersView"
        )

        self.shipping_stats_view = get_class(
            "dashboard.shipping.views", "ShippingStatsView"
        )

        self.shipping_json_view = get_class(
            "dashboard.shipping.views", "ShippingZonesGeoJsonView"
        )
        self.shipping_zona_view = get_class(
            "dashboard.shipping.views", "ShippingZonaView"
        )
        self.shipping_zones_view = get_class(
            "dashboard.shipping.views", "ShippingZonesView"
        )
        self.shipping_zones_create_view = get_class(
            "dashboard.shipping.views", "ShippingZonesCreateView"
        )
        self.shipping_zones_update_view = get_class(
            "dashboard.shipping.views", "ShippingZonesUpdateView"
        )
        self.shipping_zones_delete_view = get_class(
            "dashboard.shipping.views", "ShippingZonesDeleteView"
        )
        self.shipping_zones_hide_view = get_class(
            "dashboard.shipping.views", "ShippingZonesHideView"
        )
        self.shipping_zones_available_view = get_class(
            "dashboard.shipping.views", "ShippingZonesAvailableView"
        )

        self.shipping_couriers_list_view = get_class(
            "dashboard.shipping.views", "ShippingCouriersListView"
        )
        self.shipping_couriers_detail_view = get_class(
            "dashboard.shipping.views", "ShippingCouriersDetailView"
        )

    def get_urls(self):
        urls = [
            path(
                "active/", self.shipping_active_view.as_view(), name="shipping-active"
            ),
            path("all/", self.shipping_list_view.as_view(), name="shipping-list"),
            path(
                "orders-store/",
                self.shipping_store_view.as_view(),
                name="shipping-stores",
            ),
            path(
                "orders-courier/",
                self.shipping_couriers_view.as_view(),
                name="shipping-couriers",
            ),
            path(
                "statistic/", self.shipping_stats_view.as_view(), name="shipping-stats"
            ),
            path(
                "api/zona/",
                self.shipping_json_view.as_view(),
                name="shipping-zona-json",
            ),
            path("zona/", self.shipping_zona_view.as_view(), name="shipping-zona"),
            path("zones/", self.shipping_zones_view.as_view(), name="shipping-zones"),
            path(
                "zones/create/",
                self.shipping_zones_create_view.as_view(),
                name="shipping-create-zona",
            ),
            path(
                "zones/<int:pk>/update/",
                self.shipping_zones_update_view.as_view(),
                name="shipping-update-zona",
            ),
            path(
                "zones/<int:pk>/delete/",
                self.shipping_zones_delete_view.as_view(),
                name="shipping-delete-zona",
            ),
            path(
                "zones/<int:pk>/hide/",
                self.shipping_zones_hide_view.as_view(),
                name="shipping-hide-zona",
            ),
            path(
                "zones/<int:pk>/available/",
                self.shipping_zones_available_view.as_view(),
                name="shipping-available-zona",
            ),
            path(
                "couriers/",
                self.shipping_couriers_list_view.as_view(),
                name="shipping-couriers-list",
            ),
            path(
                "couriers/<int:pk>/",
                self.shipping_couriers_detail_view.as_view(),
                name="shipping-couriers-detail",
            ),
        ]
        return self.post_process_urls(urls)
