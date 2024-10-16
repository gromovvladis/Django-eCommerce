from .abstract_models import AbstractCRMEvent
from oscar.core.loading import is_model_registered

__all__ = []

if not is_model_registered("crm", "CRMUser"):

    class CRMEvent(AbstractCRMEvent):
        pass

    __all__.append("CRMEvent")
