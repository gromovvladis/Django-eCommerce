from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PagesDashboardConfig(OscarDashboardConfig):
    label = "pages_dashboard"
    name = "oscar.apps.dashboard.pages"
    verbose_name = "Панель управления - Страницы"

    default_permissions = [
        "user.full_access",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.list_view = get_class("dashboard.pages.views", "PageListView")
        self.create_view = get_class("dashboard.pages.views", "PageCreateView")
        self.update_view = get_class("dashboard.pages.views", "PageUpdateView")
        self.delete_view = get_class("dashboard.pages.views", "PageDeleteView")

    def get_urls(self):
        """
        Get URL patterns defined for flatpage management application.
        """
        urls = [
            path("", self.list_view.as_view(), name="page-list"),
            path("create/", self.create_view.as_view(), name="page-create"),
            path("update/<str:pk>/", self.update_view.as_view(), name="page-update"),
            path("delete/<str:pk>/", self.delete_view.as_view(), name="page-delete"),
        ]
        return self.post_process_urls(urls)
