from oscar.apps.delivery.abstract_models import AbstractDeliveryZona
from oscar.core.loading import is_model_registered

__all__ = []

    
if not is_model_registered("delivery", "DeliveryZona"):

    class DeliveryZona(AbstractDeliveryZona):
        pass

    __all__.append("DeliveryZona")