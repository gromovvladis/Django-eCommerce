from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PartnersDashboardConfig(OscarDashboardConfig):
    label = "partners_dashboard"
    name = "oscar.apps.dashboard.partners"
    verbose_name = "Панель управления - Точки продажи"

    default_permissions = [
        "user.full_access",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.partner_list_view = get_class("dashboard.partners.views", "PartnerListView")
        self.partner_create_view = get_class("dashboard.partners.views", "PartnerCreateView")
        self.partner_manage_view = get_class("dashboard.partners.views", "PartnerManageView")
        self.partner_delete_view = get_class("dashboard.partners.views", "PartnerDeleteView")

        self.terminal_list_view = get_class("dashboard.partners.views", "TerminalListView")
        self.terminal_detail_view = get_class("dashboard.partners.views", "TerminalDetailView")

        self.partner_staff_create_view = get_class("dashboard.partners.views", "PartnerStaffCreateView")
        self.partner_staff_select_view = get_class("dashboard.partners.views", "PartnerStaffSelectView")
        self.partner_staff_link_view = get_class("dashboard.partners.views", "PartnerStaffLinkView")
        self.partner_staff_unlink_view = get_class("dashboard.partners.views", "PartnerStaffUnlinkView")

        self.group_list_view = get_class("dashboard.partners.views", "GroupListView")
        self.group_detail_view = get_class("dashboard.partners.views", "GroupDetailView")
        self.group_create_view = get_class("dashboard.partners.views", "GroupCreateView")
        self.group_delete_view = get_class("dashboard.partners.views", "GroupDeleteView")

        self.staff_list_view = get_class("dashboard.partners.views", "StaffListView")
        self.staff_detail_view = get_class("dashboard.partners.views", "StaffDetailView")
        self.staff_status_view = get_class("dashboard.partners.views", "StaffStatusView")
        self.staff_create_view = get_class("dashboard.partners.views", "StaffCreateView")
        self.staff_delete_view = get_class("dashboard.partners.views", "StaffDeleteView")

    def get_urls(self):
        urls = [
            path("all/", self.partner_list_view.as_view(), name="partner-list"),
            path("all/create/", self.partner_create_view.as_view(), name="partner-create"),
            path("all/<int:pk>/", self.partner_manage_view.as_view(), name="partner-manage"),
            path("all/<int:pk>/delete/", self.partner_delete_view.as_view(), name="partner-delete"),
            
            path(
                "all/<int:partner_pk>/users/add/",
                self.partner_staff_create_view.as_view(),
                name="partner-user-create",
            ),
            path(
                "all/<int:partner_pk>/users/select/",
                self.partner_staff_select_view.as_view(),
                name="partner-user-select",
            ),
            path(
                "all/<int:partner_pk>/users/<int:user_pk>/link/",
                self.partner_staff_link_view.as_view(),
                name="partner-user-link",
            ),
            path(
                "all/<int:partner_pk>/users/<int:user_pk>/unlink/",
                self.partner_staff_unlink_view.as_view(),
                name="partner-user-unlink",
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
