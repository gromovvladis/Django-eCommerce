from django.urls import path, re_path
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class UsersDashboardConfig(OscarDashboardConfig):
    label = "users_dashboard"
    name = "oscar.apps.dashboard.users"
    verbose_name = "Панель управления - Пользователи"

    default_permissions = [
        "is_staff",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.customers_view = get_class("dashboard.users.views", "CustomersView")
        self.staff_view = get_class("dashboard.users.views", "StaffView")
        self.user_detail_view = get_class("dashboard.users.views", "UserDetailView")
        self.password_reset_view = get_class(
            "dashboard.users.views", "PasswordResetView"
        )
        # self.alert_list_view = get_class(
        #     "dashboard.users.views", "ProductAlertListView"
        # )
        # self.alert_update_view = get_class(
        #     "dashboard.users.views", "ProductAlertUpdateView"
        # )
        # self.alert_delete_view = get_class(
        #     "dashboard.users.views", "ProductAlertDeleteView"
        # )

    def get_urls(self):
        urls = [
            path("customers/", self.customers_view.as_view(), name="customers"),
            path("staff/", self.staff_view.as_view(), name="staff"),
            re_path(
                r"^(?P<pk>-?\d+)/$", self.user_detail_view.as_view(), name="user-detail"
            ),
            re_path(
                r"^(?P<pk>-?\d+)/password-reset/$",
                self.password_reset_view.as_view(),
                name="user-password-reset",
            ),
            # Alerts
            # path("alerts/", self.alert_list_view.as_view(), name="user-alert-list"),
            # re_path(
            #     r"^alerts/(?P<pk>-?\d+)/delete/$",
            #     self.alert_delete_view.as_view(),
            #     name="user-alert-delete",
            # ),
            # re_path(
            #     r"^alerts/(?P<pk>-?\d+)/update/$",
            #     self.alert_update_view.as_view(),
            #     name="user-alert-update",
            # ),
        ]
        return self.post_process_urls(urls)
