from core.application import DashboardConfig
from core.loading import get_class
from django.urls import path


class OffersDashboardConfig(DashboardConfig):
    label = "offers_dashboard"
    name = "apps.dashboard.offers"
    verbose_name = "Панель управления - Предложения"

    default_permissions = ("user.full_access",)

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.list_view = get_class("dashboard.offers.views", "OfferListView")
        self.metadata_view = get_class("dashboard.offers.views", "OfferMetaDataView")
        self.condition_view = get_class("dashboard.offers.views", "OfferConditionView")
        self.benefit_view = get_class("dashboard.offers.views", "OfferBenefitView")
        self.restrictions_view = get_class(
            "dashboard.offers.views", "OfferRestrictionsView"
        )
        self.delete_view = get_class("dashboard.offers.views", "OfferDeleteView")
        self.detail_view = get_class("dashboard.offers.views", "OfferDetailView")

    def get_urls(self):
        urls = [
            path("", self.list_view.as_view(), name="offer-list"),
            # Creation
            path("new/metadata/", self.metadata_view.as_view(), name="offer-metadata"),
            path(
                "new/condition/", self.condition_view.as_view(), name="offer-condition"
            ),
            path("new/incentive/", self.benefit_view.as_view(), name="offer-benefit"),
            path(
                "new/restrictions/",
                self.restrictions_view.as_view(),
                name="offer-restrictions",
            ),
            # Update
            path(
                "<int:pk>/metadata/",
                self.metadata_view.as_view(update=True),
                name="offer-metadata",
            ),
            path(
                "<int:pk>/condition/",
                self.condition_view.as_view(update=True),
                name="offer-condition",
            ),
            path(
                "<int:pk>/incentive/",
                self.benefit_view.as_view(update=True),
                name="offer-benefit",
            ),
            path(
                "<int:pk>/restrictions/",
                self.restrictions_view.as_view(update=True),
                name="offer-restrictions",
            ),
            # Delete
            path("<int:pk>/delete/", self.delete_view.as_view(), name="offer-delete"),
            # Stats
            path("<int:pk>/", self.detail_view.as_view(), name="offer-detail"),
        ]
        return self.post_process_urls(urls)
