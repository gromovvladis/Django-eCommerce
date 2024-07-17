from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class TelegramDashboardConfig(OscarDashboardConfig):
    label = "telegram_dashboard"
    name = "oscar.apps.dashboard.telegram"
    verbose_name = "Панель управления - Telegram bot"

    default_permissions = [
        "is_staff",
    ]
    permissions_map = {
        "telegram-admin": (["is_staff"], ["partner.dashboard_access"]),
        "telegram-errors": (["is_staff"], ["partner.dashboard_access"]),
        "telegram-couriers": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.telegram_admin_view = get_class("dashboard.telegram.views", "TelegramAdminView")
        self.telegram_errors_view = get_class("dashboard.telegram.views", "TelegramErrorsView")
        self.telegram_couriers_view = get_class("dashboard.telegram.views", "TelegramCouriersView")

    def get_urls(self):
        urls = [
            path("admin/", self.telegram_admin_view.as_view(), name="telegram-admin"),
            path("errors/", self.telegram_errors_view.as_view(), name="telegram-errors"),
            path("couriers/", self.telegram_couriers_view.as_view(), name="telegram-couriers"),
            
        ]
        return self.post_process_urls(urls)
