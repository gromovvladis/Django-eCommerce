from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class CRMDashboardConfig(OscarDashboardConfig):
    label = "crm_dashboard"
    name = "oscar.apps.dashboard.crm"
    verbose_name = "Панель управления - CRM"

    default_permissions = [
        "is_staff",
    ]
    permissions_map = {
        "crm-orders": (["is_staff"], ["partner.dashboard_access"]),
        "crm-partners": (["is_staff"], ["partner.dashboard_access"]),
        "crm-staffs": (["is_staff"], ["partner.dashboard_access"]),
        "crm-products": (["is_staff"], ["partner.dashboard_access"]),
        "crm-receipts": (["is_staff"], ["partner.dashboard_access"]),
        "crm-docs": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.crm_orders_list_view = get_class("dashboard.crm.views", "CRMOrderListView")
        self.crm_partners_list_view = get_class("dashboard.crm.views", "CRMPartnerListView")
        self.crm_staffs_list_view = get_class("dashboard.crm.views", "CRMStaffListView")
        self.crm_products_list_view = get_class("dashboard.crm.views", "CRMProductListView")
        self.crm_receipts_list_view = get_class("dashboard.crm.views", "CRMReceiptListView")
        self.crm_docs_list_view = get_class("dashboard.crm.views", "CRMDocListView")

    def get_urls(self):
        urls = [
            path("orders/", self.crm_orders_list_view.as_view(), name="crm-orders"),
            path("partners/", self.crm_partners_list_view.as_view(), name="crm-partners"),
            path("staffs/", self.crm_staffs_list_view.as_view(), name="crm-staffs"),
            path("products/", self.crm_products_list_view.as_view(), name="crm-products"),
            path("receipts/", self.crm_receipts_list_view.as_view(), name="crm-receipts"),
            path("docs/", self.crm_docs_list_view.as_view(), name="crm-docs"),

        ]
        return self.post_process_urls(urls)
