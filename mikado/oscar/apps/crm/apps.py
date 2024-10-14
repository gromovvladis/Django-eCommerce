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

        self.crm_api_staff_list_view = get_class("crm.views", "CRMStaffEndpointView")
        self.crm_api_terminal_list_view = get_class("crm.views", "CRMTerminalEndpointView")
        self.crm_api_partner_list_view = get_class("crm.views", "CRMPartnerEndpointView")
        self.crm_api_product_list_view = get_class("crm.views", "CRMProductEndpointView")
        self.crm_api_receipt_list_view = get_class("crm.views", "CRMReceiptEndpointView")
        self.crm_api_docs_list_view = get_class("crm.views", "CRMDocsEndpointView")
        self.crm_api_installation_view = get_class("crm.views", "CRMInstallationEndpointView")

        self.crm_api_user_register_view = get_class("crm.views", "CRMRegisterEndpointView")
        self.crm_api_user_login_view = get_class("crm.views", "CRMLoginEndpointView")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path("api/staffs/", self.crm_api_staff_list_view.as_view(), name="api-staffs"),
            path("api/terminals/", self.crm_api_terminal_list_view.as_view(), name="api-terminals"),
            path("api/partners/", self.crm_api_partner_list_view.as_view(), name="api-partners"),
            path("api/products/", self.crm_api_product_list_view.as_view(), name="api-products"),
            path("api/receipts/", self.crm_api_receipt_list_view.as_view(), name="api-receipts"),
            path("api/docs/", self.crm_api_docs_list_view.as_view(), name="api-docs"),

            path("api/installation/event/", self.crm_api_installation_view.as_view(), name="api-installation"),
            
            path("api/user/register/", self.crm_api_user_register_view.as_view(), name="api-register"),
            path("api/user/login/", self.crm_api_user_login_view.as_view(), name="api-login"),
        ]
        return self.post_process_urls(urls)
