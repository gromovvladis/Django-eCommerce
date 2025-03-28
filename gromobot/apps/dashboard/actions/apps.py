from core.application import DashboardConfig


class ActionsDashboardConfig(DashboardConfig):
    label = "actions_dashboard"
    name = "apps.dashboard.actions"
    verbose_name = "Панель управления - Акции-Баннеры и Промо-категории"

    default_permissions = ("staff.full_access",)
