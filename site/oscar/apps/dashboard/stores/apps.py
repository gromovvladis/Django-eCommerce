from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class StoresDashboardConfig(OscarDashboardConfig):
    label = "stores_dashboard"
    name = "oscar.apps.dashboard.stores"
    verbose_name = "Панель управления - Магазины"

    default_permissions = [
        "user.full_access",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.store_list_view = get_class("dashboard.stores.views", "StoreListView")
        self.store_create_view = get_class("dashboard.stores.views", "StoreCreateView")
        self.store_manage_view = get_class("dashboard.stores.views", "StoreManageView")
        self.store_delete_view = get_class("dashboard.stores.views", "StoreDeleteView")

        self.terminal_list_view = get_class("dashboard.stores.views", "TerminalListView")
        self.terminal_detail_view = get_class("dashboard.stores.views", "TerminalDetailView")

        self.store_staff_create_view = get_class("dashboard.stores.views", "StoreStaffCreateView")
        self.store_staff_select_view = get_class("dashboard.stores.views", "StoreStaffSelectView")
        self.store_staff_link_view = get_class("dashboard.stores.views", "StoreStaffLinkView")
        self.store_staff_unlink_view = get_class("dashboard.stores.views", "StoreStaffUnlinkView")

        self.group_list_view = get_class("dashboard.stores.views", "GroupListView")
        self.group_detail_view = get_class("dashboard.stores.views", "GroupDetailView")
        self.group_create_view = get_class("dashboard.stores.views", "GroupCreateView")
        self.group_delete_view = get_class("dashboard.stores.views", "GroupDeleteView")

        self.staff_list_view = get_class("dashboard.stores.views", "StaffListView")
        self.staff_detail_view = get_class("dashboard.stores.views", "StaffDetailView")
        self.staff_status_view = get_class("dashboard.stores.views", "StaffStatusView")
        self.staff_create_view = get_class("dashboard.stores.views", "StaffCreateView")
        self.staff_delete_view = get_class("dashboard.stores.views", "StaffDeleteView")

    def get_urls(self):
        urls = [
            path("all/", self.store_list_view.as_view(), name="store-list"),
            path("all/create/", self.store_create_view.as_view(), name="store-create"),
            path("all/<int:pk>/", self.store_manage_view.as_view(), name="store-manage"),
            path("all/<int:pk>/delete/", self.store_delete_view.as_view(), name="store-delete"),
            
            path(
                "all/<int:store_pk>/staff/add/",
                self.store_staff_create_view.as_view(),
                name="store-user-create",
            ),
            path(
                "all/<int:store_pk>/staff/select/",
                self.store_staff_select_view.as_view(),
                name="store-user-select",
            ),
            path(
                "all/<int:store_pk>/staff/<int:user_pk>/link/",
                self.store_staff_link_view.as_view(),
                name="store-user-link",
            ),
            path(
                "all/<int:store_pk>/staff/<int:user_pk>/unlink/",
                self.store_staff_unlink_view.as_view(),
                name="store-user-unlink",
            ),

            path("terminals/", self.terminal_list_view.as_view(), name="terminal-list"),
            path("terminals/<int:pk>", self.terminal_detail_view.as_view(), name="terminal-detail"),

            path("groups/", self.group_list_view.as_view(), name="group-list"),
            path("groups/<int:pk>/", self.group_detail_view.as_view(), name="group-detail"),
            path("groups/add/", self.group_create_view.as_view(), name="group-create"),
            path("groups/<int:pk>/delete/", self.group_detail_view.as_view(), name="group-delete"),

            path("staffs/", self.staff_list_view.as_view(), name="staff-list"),
            path("staffs/<int:pk>/", self.staff_detail_view.as_view(), name="staff-detail"),
            path("staffs/add/", self.staff_create_view.as_view(), name="staff-create"),
            path("staffs/<int:pk>/delete/", self.staff_delete_view.as_view(), name="staff-delete"),
            path("staffs/<int:pk>/status/", self.staff_status_view.as_view(), name="staff-status"),

        ]
        return self.post_process_urls(urls)
