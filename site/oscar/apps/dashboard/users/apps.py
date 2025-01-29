from django.urls import path, re_path
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class UsersDashboardConfig(OscarDashboardConfig):
    label = "users_dashboard"
    name = "oscar.apps.dashboard.users"
    verbose_name = "Панель управления - Пользователи"

    default_permissions = [
        "user.full_access",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.customer_list_view = get_class("dashboard.users.views", "CustomerListView")
        self.user_detail_view = get_class("dashboard.users.views", "UserDetailView")

    def get_urls(self):
        urls = [
            path("customers/", self.customer_list_view.as_view(), name="customer-list"),
            re_path(
                r"^customers/(?P<pk>-?\d+)/$", self.user_detail_view.as_view(), name="user-detail"
            ),
        ]
        return self.post_process_urls(urls)
