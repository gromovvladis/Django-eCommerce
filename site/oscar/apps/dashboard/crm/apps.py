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
        self.crm_terminals_list_view = get_class(
            "dashboard.crm.views", "CRMTerminalListView"
        )
        self.crm_staffs_list_view = get_class("dashboard.crm.views", "CRMStaffListView")
        self.crm_groups_list_view = get_class(
            "dashboard.crm.views", "CRMGroupsListView"
        )
        self.crm_products_list_view = get_class(
            "dashboard.crm.views", "CRMProductListView"
        )
        self.crm_additionals_list_view = get_class(
            "dashboard.crm.views", "CRMAdditionalListView"
        )
        self.crm_docs_list_view = get_class("dashboard.crm.views", "CRMDocsListView")

    def get_urls(self):
        urls = [
            path("stores/", self.crm_stores_list_view.as_view(), name="crm-stores"),
            path(
                "terminals/",
                self.crm_terminals_list_view.as_view(),
                name="crm-terminals",
            ),
            path("staffs/", self.crm_staffs_list_view.as_view(), name="crm-staffs"),
            path("groups/", self.crm_groups_list_view.as_view(), name="crm-groups"),
            path(
                "products/", self.crm_products_list_view.as_view(), name="crm-products"
            ),
            path(
                "additionals/",
                self.crm_additionals_list_view.as_view(),
                name="crm-additionals",
            ),
            path("docs/", self.crm_docs_list_view.as_view(), name="crm-docs"),
        ]
        return self.post_process_urls(urls)
