from .abstract_models import AbstractCRMUser, AbstractCRMToken
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered("crm", "CRMToken"):

    class CRMToken(AbstractCRMToken):
        pass

    __all__.append("CRMToken")


if not is_model_registered("crm", "CRMUser"):

    class CRMUser(AbstractCRMUser):
        pass

    __all__.append("CRMUser")
