from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PartnersDashboardConfig(OscarDashboardConfig):
    label = "partners_dashboard"
    name = "oscar.apps.dashboard.partners"
    verbose_name = "Панель управления - Точки продажи"

    default_permissions = [
        "is_staff",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.list_view = get_class("dashboard.partners.views", "PartnerListView")
        self.create_view = get_class("dashboard.partners.views", "PartnerCreateView")
        self.manage_view = get_class("dashboard.partners.views", "PartnerManageView")
        self.delete_view = get_class("dashboard.partners.views", "PartnerDeleteView")

        self.user_link_view = get_class(
            "dashboard.partners.views", "PartnerUserLinkView"
        )
        self.user_unlink_view = get_class(
            "dashboard.partners.views", "PartnerUserUnlinkView"
        )
        self.user_create_view = get_class(
            "dashboard.partners.views", "PartnerUserCreateView"
        )
        self.user_select_view = get_class(
            "dashboard.partners.views", "PartnerUserSelectView"
        )
        self.user_update_view = get_class(
            "dashboard.partners.views", "PartnerUserUpdateView"
        )

        self.staff_grouplist_view = get_class("dashboard.partners.views", "StaffGroupListView")
        self.staff_group_detail_view = get_class("dashboard.partners.views", "StaffGroupDetailView")
        self.staff_group_create_view = get_class("dashboard.partners.views", "StaffGroupCreateView")

        self.staff_list_view = get_class("dashboard.partners.views", "StaffListView")
        self.staff_detail_view = get_class("dashboard.partners.views", "StaffDetailView")
        self.staff_status_view = get_class("dashboard.partners.views", "StaffStatusView")
        self.staff_delete_view = get_class("dashboard.partners.views", "StaffDeleteView")
        self.staff_list_view = get_class("dashboard.partners.views", "StaffListView")

    def get_urls(self):
        urls = [
            path("all/", self.list_view.as_view(), name="partner-list"),
            path("all/create/", self.create_view.as_view(), name="partner-create"),
            path("all/<int:pk>/", self.manage_view.as_view(), name="partner-manage"),
            path("all/<int:pk>/delete/", self.delete_view.as_view(), name="partner-delete"),
            path(
                "all/<int:partner_pk>/users/add/",
                self.user_create_view.as_view(),
                name="partner-user-create",
            ),
            path(
                "all/<int:partner_pk>/users/select/",
                self.user_select_view.as_view(),
                name="partner-user-select",
            ),
            path(
                "all/<int:partner_pk>/users/<int:user_pk>/link/",
                self.user_link_view.as_view(),
                name="partner-user-link",
            ),
            path(
                "all/<int:partner_pk>/users/<int:user_pk>/unlink/",
                self.user_unlink_view.as_view(),
                name="partner-user-unlink",
            ),
            path(
                "all/<int:partner_pk>/users/<int:user_pk>/update/",
                self.user_update_view.as_view(),
                name="partner-user-update",
            ),
            path("groups/", self.staff_grouplist_view.as_view(), name="group-list"),
            path("groups/<int:pk>/", self.staff_group_detail_view.as_view(), name="group-detail"),
            path("groups/add/", self.staff_group_create_view.as_view(), name="group-create"),

            path("staffs/", self.staff_list_view.as_view(), name="staff-list"),
            path("staffs/<int:pk>/", self.staff_detail_view.as_view(), name="staff-detail"),
            path("staffs/<int:pk>/status/", self.staff_status_view.as_view(), name="staff-status"),
            path("staffs/<int:pk>/delete/", self.staff_delete_view.as_view(), name="staff-delete"),
            path("staffs/add/", self.staff_group_create_view.as_view(), name="staff-create"),

        ]
        return self.post_process_urls(urls)
