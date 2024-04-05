from oscar.apps.address.abstract_models import AbstractUserAddress
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered("address", "UserAddress"):

    class UserAddress(AbstractUserAddress):
        pass

    __all__.append("UserAddress")