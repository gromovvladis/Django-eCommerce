from core.application import DashboardConfig
from core.loading import get_class
from django.urls import path


class RangesDashboardConfig(DashboardConfig):
    label = "ranges_dashboard"
    name = "apps.dashboard.ranges"
    verbose_name = "Панель управления - Ассортименты"

    default_permissions = (
        "staff.full_access",
        "catalogue.full_access",
    )

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.list_view = get_class("dashboard.ranges.views", "RangeListView")
        self.create_view = get_class("dashboard.ranges.views", "RangeCreateView")
        self.update_view = get_class("dashboard.ranges.views", "RangeUpdateView")
        self.delete_view = get_class("dashboard.ranges.views", "RangeDeleteView")
        self.products_view = get_class("dashboard.ranges.views", "RangeProductListView")
        self.reorder_view = get_class("dashboard.ranges.views", "RangeReorderView")

    def get_urls(self):
        urlpatterns = [
            path("", self.list_view.as_view(), name="range-list"),
            path("create/", self.create_view.as_view(), name="range-create"),
            path("<int:pk>/", self.update_view.as_view(), name="range-update"),
            path("<int:pk>/delete/", self.delete_view.as_view(), name="range-delete"),
            path(
                "<int:pk>/products/",
                self.products_view.as_view(),
                name="range-products",
            ),
            path(
                "<int:pk>/reorder/", self.reorder_view.as_view(), name="range-reorder"
            ),
        ]
        return self.post_process_urls(urlpatterns)
