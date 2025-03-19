from decimal import Decimal as D
from functools import lru_cache

from core.loading import get_model
from shapely.geometry import Point, Polygon

ShippingZona = get_model("shipping", "ShippingZona")


class ZonesUtils:

    @classmethod
    @lru_cache(maxsize=128)
    def zones(self):
        return ShippingZona.objects.filter(isHide=False)

    @classmethod
    def available_zones(self):
        """Return list of available shipping zones."""
        return ShippingZona.objects.filter(isHide=False, isAvailable=True)

    @classmethod
    @lru_cache(maxsize=128)
    def zones_polygon(self, zones=None):
        polygon_zones = {}
        if zones is None:
            zones = self.zones()

        for zona in zones:
            coords = []
            for crd in zona.coords.split("],"):
                crd = crd.replace("]", "").replace("[", "")
                crd = crd.split(",")
                coords.append((D(crd[0]), D(crd[1])))

            polygon_zones[zona.id] = Polygon(coords)

        return polygon_zones

    @classmethod
    def zona_id(self, coords, zones=None) -> int:
        """Получает координы обекта, возвращает id зоны доставки, либо 0, если адрес вне зоны доставки"""
        zones = self.zones_polygon(zones)
        coords_point = Point(coords[0], coords[1])

        for zonaId, zona in zones.items():
            if coords_point.within(zona):
                return zonaId

        return 0

    # ==================================================

    @classmethod
    def min_order_for_zona(self, zona_id, zones=None) -> int:
        try:
            if zones is None:
                zones = self.available_zones()
            zona = zones.get(number=zona_id)
            return zona.order_price
        except Exception:
            return 700

    @classmethod
    def is_zona_available(self, zona_id, zones=None) -> bool:
        try:
            if zones is None:
                zones = self.available_zones()
            zones.get(number=zona_id)
        except ShippingZona.DoesNotExist:
            return False

        return True
