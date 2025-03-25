from core.application import Config


class VoucherConfig(Config):
    label = "voucher"
    name = "apps.webshop.voucher"
    verbose_name = "Промокод"

    def ready(self):
        # pylint: disable=unused-import
        from . import receivers
