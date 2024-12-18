from oscar.core.application import OscarConfig
from django.urls import path
from oscar.core.loading import get_class
from django.views.decorators.csrf import csrf_exempt

class PaymentConfig(OscarConfig):
    label = "payment"
    name = "oscar.apps.payment"
    verbose_name = "Платежи"

    def ready(self):
            self.update_payment_view = get_class("payment.views", "UpdatePayment")
            self.yookassa_payment_handler_view = get_class("payment.views", "YookassaPaymentHandler")
            self.evotor_payment_handler_view = get_class("payment.views", "EvotorPaymentHandler")

    def get_urls(self):
        urls = [
            path("update/<int:pk>/", self.update_payment_view.as_view(), name="update"),
            path("api/yookassa/", csrf_exempt(self.yookassa_payment_handler_view.as_view()), name="yokassa",),
            path("api/evotor/<int:pk>/", csrf_exempt(self.evotor_payment_handler_view.as_view()), name="evotor",),
        ]
        return self.post_process_urls(urls)