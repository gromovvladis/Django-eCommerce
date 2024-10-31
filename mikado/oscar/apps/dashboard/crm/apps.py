from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class CRMDashboardConfig(OscarDashboardConfig):
    label = "crm_dashboard"
    name = "oscar.apps.dashboard.crm"
    verbose_name = "Панель управления - CRM"

    default_permissions = [
        "user.full_access",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.crm_orders_list_view = get_class("dashboard.crm.views", "CRMOrderListView")
        self.crm_partners_list_view = get_class("dashboard.crm.views", "CRMPartnerListView")
        self.crm_terminals_list_view = get_class("dashboard.crm.views", "CRMTerminalListView")
        self.crm_staffs_list_view = get_class("dashboard.crm.views", "CRMStaffListView")
        self.crm_products_list_view = get_class("dashboard.crm.views", "CRMProductListView")
        self.crm_receipts_list_view = get_class("dashboard.crm.views", "CRMReceiptListView")
        self.crm_docs_list_view = get_class("dashboard.crm.views", "CRMDocListView")

    def get_urls(self):
        urls = [
            path("partners/", self.crm_partners_list_view.as_view(), name="crm-partners"),
            path("terminals/", self.crm_terminals_list_view.as_view(), name="crm-terminals"),
            path("staffs/", self.crm_staffs_list_view.as_view(), name="crm-staffs"),
            path("orders/", self.crm_orders_list_view.as_view(), name="crm-orders"),
            path("products/", self.crm_products_list_view.as_view(), name="crm-products"),
            path("receipts/", self.crm_receipts_list_view.as_view(), name="crm-receipts"),
            path("docs/", self.crm_docs_list_view.as_view(), name="crm-docs"),

        ]
        return self.post_process_urls(urls)
