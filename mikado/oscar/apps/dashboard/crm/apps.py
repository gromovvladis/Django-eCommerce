from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class CRMDashboardConfig(OscarDashboardConfig):
    label = "crm"
    name = "oscar.apps.dashboard.crm"
    verbose_name = "Панель управления - CRM"

    namespace = "crm"

    default_permissions = [
        "is_staff",
    ]
    permissions_map = {
        "crm-orders": (["is_staff"], ["partner.dashboard_access"]),
        "crm-stop-list": (["is_staff"], ["partner.dashboard_access"]),
        "crm-price-list": (["is_staff"], ["partner.dashboard_access"]),
        "crm-courier": (["is_staff"], ["partner.dashboard_access"]),
        "crm-delivery": (["is_staff"], ["partner.dashboard_access"]),
    }

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.crm_orders_list_view = get_class("dashboard.crm.views", "CRMOrderListView")
        self.crm_partners_list_view = get_class("dashboard.crm.views", "CRMPartnerListView")
        self.crm_staffs_list_view = get_class("dashboard.crm.views", "CRMStaffListView")
        self.crm_products_list_view = get_class("dashboard.crm.views", "CRMProductListView")
        self.crm_receipts_list_view = get_class("dashboard.crm.views", "CRMReceiptListView")
        self.crm_docs_list_view = get_class("dashboard.crm.views", "CRMDocListView")

        self.crm_api_staff_list_view = get_class("dashboard.crm.views", "CRMStaffEndpointView")
        self.crm_api_terminal_list_view = get_class("dashboard.crm.views", "CRMTerminalEndpointView")
        self.crm_api_partner_list_view = get_class("dashboard.crm.views", "CRMPartnerEndpointView")
        self.crm_api_product_list_view = get_class("dashboard.crm.views", "CRMProductEndpointView")
        self.crm_api_receipt_list_view = get_class("dashboard.crm.views", "CRMReceiptEndpointView")
        self.crm_api_docs_list_view = get_class("dashboard.crm.views", "CRMDocsEndpointView")
        self.crm_api_token_view = get_class("dashboard.crm.views", "CRMTokenEndpointView")
        self.crm_api_subscription_view = get_class("dashboard.crm.views", "CRMSubscriptionEndpointView")

        self.crm_api_user_create_view = get_class("dashboard.crm.views", "CRMUserCreateEndpointView")
        self.crm_api_user_verify_view = get_class("dashboard.crm.views", "CRMUserVerifyEndpointView")

    def get_urls(self):
        urls = [
            path("orders/", self.crm_orders_list_view.as_view(), name="crm-orders"),
            path("partners/", self.crm_partners_list_view.as_view(), name="crm-partners"),
            path("staffs/", self.crm_staffs_list_view.as_view(), name="crm-staffs"),
            path("products/", self.crm_products_list_view.as_view(), name="crm-products"),
            path("receipts/", self.crm_receipts_list_view.as_view(), name="crm-receipts"),
            path("docs/", self.crm_docs_list_view.as_view(), name="crm-docs"),
        
            
            path("api/staffs/", self.crm_api_staff_list_view.as_view(), name="crm-api-staffs"),
            path("api/terminals/", self.crm_api_terminal_list_view.as_view(), name="crm-api-terminals"),
            path("api/partners/", self.crm_api_partner_list_view.as_view(), name="crm-api-partners"),
            path("api/products/", self.crm_api_product_list_view.as_view(), name="crm-api-products"),
            path("api/receipts/", self.crm_api_receipt_list_view.as_view(), name="crm-api-receipts"),
            path("api/docs/", self.crm_api_docs_list_view.as_view(), name="crm-api-docs"),

            path("api/subscription/setup", self.crm_api_subscription_view.as_view(), name="crm-api-setup"),
            path("api/subscription/event", self.crm_api_subscription_view.as_view(), name="crm-api-event"),
            
            path("api/user/token", self.crm_api_token_view.as_view(), name="crm-api-token"),
            path("api/user/create", self.crm_api_user_create_view.as_view(), name="crm-api-user-create"),
            path("api/user/verify", self.crm_api_user_verify_view.as_view(), name="crm-api-user-verify"),


        ]
        return self.post_process_urls(urls)
