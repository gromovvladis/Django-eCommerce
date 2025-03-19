from django.urls import path
from core.application import DashboardConfig
from core.loading import get_class


class ReportsDashboardConfig(DashboardConfig):
    label = "reports_dashboard"
    name = "apps.dashboard.reports"
    verbose_name = "Панель управления - Отчеты"

    default_permissions = [
        "user.full_access",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.index_view = get_class("dashboard.reports.views", "IndexView")

    def get_urls(self):
        urls = [
            path("", self.index_view.as_view(), name="reports-index"),
        ]
        return self.post_process_urls(urls)
