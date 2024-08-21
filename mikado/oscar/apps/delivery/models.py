from oscar.apps.delivery.abstract_models import AbstractDeliveryZona,  AbstractCourier, AbstractCourierShift, AbstractDeliveryOrder, AbstractTrip, AbstractRoute, AbstractDeliverySession
from oscar.core.loading import is_model_registered

__all__ = []

    
if not is_model_registered("delivery", "DeliveryZona"):

    class DeliveryZona(AbstractDeliveryZona):
        pass

    __all__.append("DeliveryZona")


if not is_model_registered("delivery", "Courier"):

    class Courier(AbstractCourier):
        pass

    __all__.append("Courier")

    
if not is_model_registered("delivery", "CourierShift"):

    class CourierShift(AbstractCourierShift):
        pass

    __all__.append("CourierShift")

    
if not is_model_registered("delivery", "DeliveryOrder"):

    class DeliveryOrder(AbstractDeliveryOrder):
        pass

    __all__.append("DeliveryOrder")

    
if not is_model_registered("delivery", "Trip"):

    class Trip(AbstractTrip):
        pass

    __all__.append("Trip")


if not is_model_registered("delivery", "Route"):

    class Route(AbstractRoute):
        pass

    __all__.append("Route")


if not is_model_registered("delivery", "DeliverySession"):

    class DeliverySession(AbstractDeliverySession):
        pass

    __all__.append("DeliverySession")