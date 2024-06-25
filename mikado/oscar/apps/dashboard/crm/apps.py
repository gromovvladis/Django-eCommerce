from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class CRMDashboardConfig(OscarDashboardConfig):
    label = "crm_dashboard"
    name = "oscar.apps.dashboard.crm"
    verbose_name = "Панель управления - Tillypad"

    default_permissions = [
        "is_staff",
    ]
    permissions_map = {
        "crm-orders": (["is_staff"], ["partner.dashboard_access"]),
        "crm-stop-list": (["is_staff"], ["partner.dashboard_access"]),
        "crm-price-list": (["is_staff"], ["partner.dashboard_access"]),
        "crm-courier": (["is_staff"], ["partner.dashboard_access"]),
        "crm-delivery": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.crm_orders_view = get_class("dashboard.crm.views", "CRMOrdersView")
        self.crm_stop_list_view = get_class("dashboard.crm.views", "CRMStopListView")
        self.crm_price_list_view = get_class("dashboard.crm.views", "CRMPriceListView")
        self.crm_couriers_view = get_class("dashboard.crm.views", "CRMCouriersView")
        self.crm_delivery_view = get_class("dashboard.crm.views", "CRMDeliveryView")

    def get_urls(self):
        urls = [
            path("", self.crm_orders_view.as_view(), name="crm-orders"),
            path("stop-list/", self.crm_stop_list_view.as_view(), name="crm-stop-list"),
            path("price-list/", self.crm_price_list_view.as_view(), name="crm-price-list"),
            path("couriers/", self.crm_couriers_view.as_view(), name="crm-couriers"),
            path("delivery/", self.crm_delivery_view.as_view(), name="crm-delivery"),
        ]
        return self.post_process_urls(urls)
