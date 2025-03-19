from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from core.application import Config
from core.loading import get_class


class PaymentConfig(Config):
    label = "payment"
    name = "apps.webshop.payment"
    verbose_name = "Платежи"

    def ready(self):
        from . import receivers

        super().ready()
        self.update_payment_view = get_class("webshop.payment.views", "UpdatePayment")
        self.yookassa_payment_handler_view = get_class(
            "webshop.payment.views", "YookassaPaymentHandler"
        )

    def get_urls(self):
        urls = [
            path("update/<int:pk>/", self.update_payment_view.as_view(), name="update"),
            path(
                "api/yookassa/",
                csrf_exempt(self.yookassa_payment_handler_view.as_view()),
                name="yokassa",
            ),
        ]
        return self.post_process_urls(urls)
