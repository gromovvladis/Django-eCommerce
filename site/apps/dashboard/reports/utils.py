from core.loading import get_class, get_classes

OrderReportGenerator = get_class("webshop.order.reports", "OrderReportGenerator")
ProductReportGenerator, UserReportGenerator = get_classes(
    "webshop.analytics.reports", ["ProductReportGenerator", "UserReportGenerator"]
)
OpenBasketReportGenerator, SubmittedBasketReportGenerator = get_classes(
    "webshop.basket.reports", ["OpenBasketReportGenerator", "SubmittedBasketReportGenerator"]
)
OfferReportGenerator = get_class("webshop.offer.reports", "OfferReportGenerator")
VoucherReportGenerator = get_class("webshop.voucher.reports", "VoucherReportGenerator")
EvotorReportGenerator = get_class("evotor.reports", "EvotorReportGenerator")


class GeneratorRepository(object):
    generators = [
        EvotorReportGenerator,
        OrderReportGenerator,
        ProductReportGenerator,
        UserReportGenerator,
        OpenBasketReportGenerator,
        SubmittedBasketReportGenerator,
        VoucherReportGenerator,
        OfferReportGenerator,
    ]

    def get_report_generators(self):
        return self.generators

    def get_generator(self, code):
        for generator in self.generators:
            if generator.code == code:
                return generator
        return None
