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
        self.customer_list_view = get_class("dashboard.users.views", "CustomerListView")
        self.user_detail_view = get_class("dashboard.users.views", "UserDetailView")
        # self.password_reset_view = get_class(
        #     "dashboard.users.views", "PasswordResetView"
        # )

    def get_urls(self):
        urls = [
            path("customers/", self.customer_list_view.as_view(), name="customer-list"),
            re_path(
                r"^(?P<pk>-?\d+)/$", self.user_detail_view.as_view(), name="user-detail"
            ),
            # re_path(
            #     r"^(?P<pk>-?\d+)/password-reset/$",
            #     self.password_reset_view.as_view(),
            #     name="user-password-reset",
            # ),
        ]
        return self.post_process_urls(urls)
