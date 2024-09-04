from shapely.geometry import Point, Polygon
from decimal import Decimal as D
from functools import lru_cache

from oscar.core.loading import get_model
DeliveryZona = get_model("delivery", "DeliveryZona")

class ZonesUtils:
    
    @classmethod
    @lru_cache(maxsize=128)  
    def getZones(self):
        return DeliveryZona.objects.filter(isHide=False)
    
    @classmethod
    def getAvailableZones(self):
        """Return list of available delivery zones."""
        return DeliveryZona.objects.filter(isHide=False, isAvailable=True)

    @classmethod
    @lru_cache(maxsize=128)  
    def getZonesPolygon(self, zones=None):

        polygon_zones = {}

        if zones is None:
            zones = self.getZones()
        
        for zona in zones:
            coords = []
            for crd in zona.coords.split('],'):
                crd = crd.replace("]", "").replace("[", "")
                crd = crd.split(",")
                coords.append((D(crd[0]), D(crd[1])))

            polygon_zones[zona.id] = Polygon(coords)

        return polygon_zones

    @classmethod
    def getZonaId(self, coords, zones=None) -> int:
        """Получает координы обекта, возвращает id зоны доставки, либо 0, если адрес вне зоны доставки"""
        zones = self.getZonesPolygon(zones)

        coords_point = Point(coords[0], coords[1])

        for zonaId, zona in zones.items():
            if coords_point.within(zona):
                return zonaId

        return 0


# ==================================================
    
    @classmethod
    def getMinOrderForZona(self, zona_id, zones=None) -> int:

        min_order = 700

        try:
            if zones is None:
                zones = self.getAvailableZones()
            zona = zones.get(number=zona_id)
            min_order = zona.order_price
        except Exception:
            return min_order
        
        return min_order

    @classmethod
    def IsZonaAvailable(self, zona_id, zones=None) -> bool:
        try:
            if zones is None:
                zones = self.getAvailableZones()
            isAvailable = zones.get(number=zona_id)
        except Exception:
            return False
        
        return True
    
