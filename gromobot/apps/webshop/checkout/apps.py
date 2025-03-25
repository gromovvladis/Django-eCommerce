from core.application import Config
from core.loading import get_class
from django.contrib.auth.decorators import login_required
from django.urls import path


class CheckoutConfig(Config):
    label = "checkout"
    name = "apps.webshop.checkout"
    verbose_name = "Оформление заказа"

    namespace = "checkout"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from . import receivers

        self.index_view = get_class("webshop.checkout.views", "IndexView")

        self.checkoutview_view = get_class("webshop.checkout.views", "CheckoutView")
        self.payment_details_view = get_class("webshop.checkout.views", "PaymentDetailsView")
        self.update_totals_view = get_class("webshop.checkout.views", "UpdateTotalsView")
        self.thankyou_view = get_class("webshop.checkout.views", "ThankYouView")

        self.add_voucher_view = get_class("webshop.checkout.views", "VoucherAddView")
        self.remove_voucher_view = get_class("webshop.checkout.views", "VoucherRemoveView")

    def get_urls(self):
        urls = [
            path("checkout", self.index_view.as_view(), name="index"),
            path(
                "",
                self.checkoutview_view.as_view(),
                name="checkoutview",
            ),
            path(
                "payment-details/",
                self.payment_details_view.as_view(),
                name="payment-details",
            ),
            path("thank-you/", self.thankyou_view.as_view(), name="thank-you"),
            path(
                "api/update-totals/",
                self.update_totals_view.as_view(),
                name="update-totals",
            ),
            path("vouchers/add/", self.add_voucher_view.as_view(), name="vouchers-add"),
            path(
                "vouchers/<int:pk>/remove/",
                self.remove_voucher_view.as_view(),
                name="vouchers-remove",
            ),
        ]
        return self.post_process_urls(urls)

    def get_url_decorator(self, pattern):
        return login_required
