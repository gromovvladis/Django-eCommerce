from oscar.core.application import OscarConfig


class VoucherConfig(OscarConfig):
    label = "voucher"
    name = "oscar.apps.voucher"
    verbose_name = "Промокод"

    def ready(self):
        # pylint: disable=unused-import
        from . import receivers
