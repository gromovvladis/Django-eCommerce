from decimal import Decimal as D

from core.loading import get_model
from shapely.geometry import Point, Polygon

ShippingZona = get_model("shipping", "ShippingZona")


class ZonesUtils:

    _zones = None
    _available_zones = None
    _zones_polygon = None

    def zones(self):
        if self._zones is None:
            self._zones = ShippingZona.objects.filter(isHide=False)
        return self._zones

    def available_zones(self):
        """Return list of available shipping zones."""
        if self._available_zones is None:
            self._available_zones = ShippingZona.objects.filter(
                isHide=False, isAvailable=True
            )
        return self._available_zones

    def zones_polygon(self):
        if self._zones_polygon is None:
            self._zones_polygon = {
                zona.id: Polygon(
                    [
                        (D(coord.split(",")[0]), D(coord.split(",")[1]))
                        for coord in zona.coords.replace("][", "],[").split("],")
                    ]
                )
                for zona in self.zones()
            }

        return self._zones_polygon

    def get_zona_id(self, coords) -> int:
        """Получает координы обекта, возвращает id зоны доставки, либо 0, если адрес вне зоны доставки"""
        polygon_zones = self.zones_polygon()
        coords_point = Point(coords[0], coords[1])

        for zonaId, zona in polygon_zones.items():
            if coords_point.within(zona):
                return zonaId

        return 0

    # helpers calculate

    def min_order_for_zona(self, zona_id) -> int:
        zona = self._get_zona(zona_id)
        if zona:
            return zona.order_price
        return 700

    def is_zona_available(self, zona_id) -> bool:
        return self._get_zona(zona_id) is not None

    def zona_charge(self, zona_id):
        zona = self._get_zona(zona_id)
        if zona:
            return zona.shipping_price
        return 0

    def min_order(self, zona_id):
        zona = self._get_zona(zona_id)
        if zona:
            return zona.order_price
        return 700  # default value

    # Общий метод для получения зоны
    def _get_zona(self, zona_id):
        try:
            return self.available_zones().get(number=zona_id)
        except ShippingZona.DoesNotExist:
            return None
