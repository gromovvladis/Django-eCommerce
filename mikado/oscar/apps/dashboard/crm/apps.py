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
        self.crm_stores_list_view = get_class("dashboard.crm.views", "CRMStoreListView")
        self.crm_terminals_list_view = get_class("dashboard.crm.views", "CRMTerminalListView")
        self.crm_staffs_list_view = get_class("dashboard.crm.views", "CRMStaffListView")
        self.crm_groups_list_view = get_class("dashboard.crm.views", "CRMGroupsListView")
        self.crm_products_list_view = get_class("dashboard.crm.views", "CRMProductListView")
        self.crm_additionals_list_view = get_class("dashboard.crm.views", "CRMAdditionalListView")
        self.crm_docs_list_view = get_class("dashboard.crm.views", "CRMDocsListView")

        self.crm_accept_list_view = get_class("dashboard.crm.views", "CRMAcceptListView")
        self.crm_revaluation_list_view = get_class("dashboard.crm.views", "CRMRevaluationListView")
        self.crm_write_off_list_view = get_class("dashboard.crm.views", "CRMWriteOffListView")
        self.crm_inventory_list_view = get_class("dashboard.crm.views", "CRMInventoryListView")
        self.crm_session_list_view = get_class("dashboard.crm.views", "CRMSessionListView")
        self.crm_cash_list_view = get_class("dashboard.crm.views", "CRMCashListView")
        self.crm_report_list_view = get_class("dashboard.crm.views", "CRMReportListView")

        self.crm_event_list_view = get_class("dashboard.crm.views", "CRMEventListView")

    def get_urls(self):
        urls = [
            path("stores/", self.crm_stores_list_view.as_view(), name="crm-stores"),
            path("terminals/", self.crm_terminals_list_view.as_view(), name="crm-terminals"),
            path("staffs/", self.crm_staffs_list_view.as_view(), name="crm-staffs"),
            path("groups/", self.crm_groups_list_view.as_view(), name="crm-groups"),
            path("products/", self.crm_products_list_view.as_view(), name="crm-products"),
            path("additionals/", self.crm_additionals_list_view.as_view(), name="crm-additionals"),
            path("docs/", self.crm_docs_list_view.as_view(), name="crm-docs"),
            
            path("accepts/", self.crm_accept_list_view.as_view(), name="crm-accept"),
            path("revaluations/", self.crm_revaluation_list_view.as_view(), name="crm-revaluation"),
            path("write-offs/", self.crm_write_off_list_view.as_view(), name="crm-write-off"),
            path("inventories/", self.crm_inventory_list_view.as_view(), name="crm-inventory"),
            path("sessions/", self.crm_session_list_view.as_view(), name="crm-sessions"),
            path("cashs/", self.crm_cash_list_view.as_view(), name="crm-cash"),
            path("reports/", self.crm_report_list_view.as_view(), name="crm-report"),

            path("events/", self.crm_event_list_view.as_view(), name="crm-events"),

        ]
        return self.post_process_urls(urls)
