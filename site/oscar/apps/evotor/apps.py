from django.urls import path, re_path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class EvotorConfig(OscarConfig):
    label = "evotor"
    name = "oscar.apps.evotor"
    verbose_name = "Эвотор Облако"

    namespace = "evotor"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from . import receivers

        super().ready()

        self.evotor_api_store_view = get_class(
            "evotor.views", "EvotorStoreEndpointView"
        )
        self.evotor_api_terminal_view = get_class(
            "evotor.views", "EvotorTerminalEndpointView"
        )
        self.evotor_api_staff_view = get_class(
            "evotor.views", "EvotorStaffEndpointView"
        )
        self.evotor_api_role_view = get_class("evotor.views", "EvotorRoleEndpointView")
        self.evotor_api_product_view = get_class(
            "evotor.views", "EvotorProductEndpointView"
        )
        self.evotor_api_docs_view = get_class("evotor.views", "EvotorDocsEndpointView")
        self.evotor_api_installation_view = get_class(
            "evotor.views", "EvotorInstallationEndpointView"
        )

        self.evotor_api_user_login_view = get_class(
            "evotor.views", "EvotorLoginEndpointView"
        )

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path(
                "api/stores/", self.evotor_api_store_view.as_view(), name="api-stores"
            ),
            path(
                "api/terminals/",
                self.evotor_api_terminal_view.as_view(),
                name="api-terminals",
            ),
            path(
                "api/staffs/", self.evotor_api_staff_view.as_view(), name="api-staffs"
            ),
            path("api/roles/", self.evotor_api_role_view.as_view(), name="api-roles"),
            path(
                "api/v1/inventories/stores/<str:store_id>/products/",
                self.evotor_api_product_view.as_view(),
                name="api-products",
            ),
            path("api/docs/", self.evotor_api_docs_view.as_view(), name="api-docs"),
            path(
                "api/installation/event/",
                self.evotor_api_installation_view.as_view(),
                name="api-installation",
            ),
            path(
                "api/user/login/",
                self.evotor_api_user_login_view.as_view(),
                name="api-login",
            ),
            re_path(r"^api/.*$", self.evotor_api_product_view.as_view()),
        ]
        return self.post_process_urls(urls)
