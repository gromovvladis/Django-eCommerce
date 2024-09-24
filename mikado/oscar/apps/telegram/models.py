from oscar.apps.telegram import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered("telegram", "TelegramMessage"):

    class TelegramMessage(abstract_models.AbstractTelegramMessage):
        pass

    __all__.append("TelegramMessage")
