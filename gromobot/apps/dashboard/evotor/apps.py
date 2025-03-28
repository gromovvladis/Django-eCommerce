from core.application import DashboardConfig
from core.loading import get_class
from django.urls import path


class EvotorDashboardConfig(DashboardConfig):
    label = "evotor_dashboard"
    name = "apps.dashboard.evotor"
    verbose_name = "Панель управления - Облако Эвотор"

    default_permissions = ("user.full_access",)

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.evotor_stores_list_view = get_class(
            "dashboard.evotor.views", "EvotorStoreListView"
        )
        self.evotor_terminals_list_view = get_class(
            "dashboard.evotor.views", "EvotorTerminalListView"
        )
        self.evotor_staffs_list_view = get_class(
            "dashboard.evotor.views", "EvotorStaffListView"
        )
        self.evotor_groups_list_view = get_class(
            "dashboard.evotor.views", "EvotorGroupsListView"
        )
        self.evotor_products_list_view = get_class(
            "dashboard.evotor.views", "EvotorProductListView"
        )
        self.evotor_additionals_list_view = get_class(
            "dashboard.evotor.views", "EvotorAdditionalListView"
        )
        self.evotor_docs_list_view = get_class(
            "dashboard.evotor.views", "EvotorDocsListView"
        )

    def get_urls(self):
        urls = [
            path(
                "stores/", self.evotor_stores_list_view.as_view(), name="evotor-stores"
            ),
            path(
                "terminals/",
                self.evotor_terminals_list_view.as_view(),
                name="evotor-terminals",
            ),
            path(
                "staffs/", self.evotor_staffs_list_view.as_view(), name="evotor-staffs"
            ),
            path(
                "groups/", self.evotor_groups_list_view.as_view(), name="evotor-groups"
            ),
            path(
                "products/",
                self.evotor_products_list_view.as_view(),
                name="evotor-products",
            ),
            path(
                "additionals/",
                self.evotor_additionals_list_view.as_view(),
                name="evotor-additionals",
            ),
            path("docs/", self.evotor_docs_list_view.as_view(), name="evotor-docs"),
        ]
        return self.post_process_urls(urls)
