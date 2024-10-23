from oscar.apps.address.abstract_models import AbstractPartnerAddress
from oscar.apps.partner.abstract_models import (
    AbstractPartner,
    AbstractTerminal,
    AbstractBarCode,
    AbstractStockAlert,
    AbstractStockRecord,
)
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered("partner", "Partner"):

    class Partner(AbstractPartner):
        pass

    __all__.append("Partner")


if not is_model_registered("partner", "Terminal"):

    class Terminal(AbstractTerminal):
        pass

    __all__.append("Terminal")


if not is_model_registered("partner", "PartnerAddress"):

    class PartnerAddress(AbstractPartnerAddress):
        pass

    __all__.append("PartnerAddress")


if not is_model_registered("partner", "BarCode"):

    class BarCode(AbstractBarCode):
        pass

    __all__.append("BarCode")


if not is_model_registered("partner", "StockRecord"):

    class StockRecord(AbstractStockRecord):
        pass

    __all__.append("StockRecord")


if not is_model_registered("partner", "StockAlert"):

    class StockAlert(AbstractStockAlert):
        pass

    __all__.append("StockAlert")
