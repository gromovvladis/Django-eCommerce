# pylint: disable=wildcard-import, unused-wildcard-import

"""
Promo goods
"""
from oscar.apps.home.abstract_models import *
from oscar.core.loading import is_model_registered

__all__ = []

if not is_model_registered("home", "Action"):

    class Action(AbstractAction):
        pass

    __all__.append("Action")

if not is_model_registered("home", "PromoCategory"):

    class PromoCategory(AbstractPromoCategory):
        pass

    __all__.append("PromoCategory")
