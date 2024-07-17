from django.urls import path

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PaymentsDashboardConfig(OscarDashboardConfig):
    label = "payments_dashboard"
    name = "oscar.apps.dashboard.payments"
    verbose_name = "Панель управления - Онлайн-оплата Yookassa"

    default_permissions = [
        "is_staff",
    ]

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.payments_list_view = get_class("dashboard.payments.views", "PaymentsListView")
        self.payment_detail_view = get_class("dashboard.payments.views", "PaymentDetailView")
        self.update_payment_view = get_class("dashboard.payments.views", "UpdatePaymentView")
        self.refund_payment_view = get_class("dashboard.payments.views", "RefundPaymentView")

    def get_urls(self):
        urls = [
            path("", self.payments_list_view.as_view(), name="payments-list"),
            path("<str:number>/", self.payment_detail_view.as_view(), name="payment-detail"),
            path(
                "<str:number>/update-payment/",
                self.update_payment_view.as_view(), 
                name='update-payment'
            ),
            path(
                "<str:number>/refund-payment/",
                self.refund_payment_view.as_view(), 
                name='refund-payment'
            ),
        ]
        return self.post_process_urls(urls)
