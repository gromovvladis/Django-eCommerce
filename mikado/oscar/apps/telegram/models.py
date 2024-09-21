from oscar.apps.telegram import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered("telegram", "TelegramMassage"):

    class TelegramMassage(abstract_models.AbstractTelegramMassage):
        pass

    __all__.append("TelegramMassage")


if not is_model_registered("telegram", "TelegramUser"):

    class TelegramUser(abstract_models.AbstractTelegramUser):
        pass

    __all__.append("TelegramUser")
