from oscar.apps.customer.abstract_models import AbstractOrderReview, AbstractGroupEvotor
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered("customer", "OrderReview"):

    class OrderReview(AbstractOrderReview):
        pass

    __all__.append("OrderReview")

if not is_model_registered("auth", "GroupEvotor"):

    class GroupEvotor(AbstractGroupEvotor):
        pass

    __all__.append("GroupEvotor")
