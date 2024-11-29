from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CRMConfig(OscarConfig):
    label = "crm"
    name = "oscar.apps.crm"
    verbose_name = "API Evotor"

    namespace = "crm"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        super().ready()

        self.crm_api_staff_view = get_class("crm.views", "CRMStaffEndpointView")
        self.crm_api_role_view = get_class("crm.views", "CRMRoleEndpointView")
        self.crm_api_terminal_view = get_class("crm.views", "CRMTerminalEndpointView")
        self.crm_api_store_view = get_class("crm.views", "CRMStoreEndpointView")
        self.crm_api_product_view = get_class("crm.views", "CRMProductEndpointView")
        self.crm_api_docs_view = get_class("crm.views", "CRMDocsEndpointView")
        self.crm_api_installation_view = get_class("crm.views", "CRMInstallationEndpointView")

        self.crm_api_user_login_view = get_class("crm.views", "CRMLoginEndpointView")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path("api/staffs/", self.crm_api_staff_view.as_view(), name="api-staffs"),
            path("api/roles/", self.crm_api_role_view.as_view(), name="api-staffs"),
            path("api/terminals/", self.crm_api_terminal_view.as_view(), name="api-terminals"),
            path("api/stores/", self.crm_api_store_view.as_view(), name="api-stores"),
            path("api/inventories/stores/<str:store_id>/products/", self.crm_api_product_view.as_view(), name="api-products"),
            path("api/docs/", self.crm_api_docs_view.as_view(), name="api-docs"),

            path("api/installation/event/", self.crm_api_installation_view.as_view(), name="api-installation"),
            
            path("api/user/login/", self.crm_api_user_login_view.as_view(), name="api-login"),
        ]
        return self.post_process_urls(urls)
