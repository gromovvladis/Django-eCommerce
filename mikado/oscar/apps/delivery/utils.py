import json
from django.conf import settings
from shapely.geometry import Point, Polygon
from decimal import Decimal as D

from oscar.core.loading import get_model


_dir = settings.STATIC_PRIVATE_ROOT

class ZonesUtils:

    
    def getZones(self):
        DeliveryZona = get_model("delivery", "DeliveryZona")
        return DeliveryZona.objects.filter(isHide=False)


    def getZonesPolygon(self):

        zones = self.getZones()
        polygon_zones = {}
        
        for zona in zones:

            coords = []
            for crd in zona.coords.split('],'):
                crd = crd.replace("]", "").replace("[", "")
                crd = crd.split(",")
                coords.append((D(crd[0]), D(crd[1])))

            # polygon_zones[zona.number] = [zona.isAvailable, Polygon(coords)]  
            polygon_zones[zona.number] = Polygon(coords)


        return polygon_zones


    def getZonaId(self, coords, zones=None) -> int:
        """Получает координы обекта, возвращает id зоны доставки, либо 0, если адрес вне зоны доставки"""
        coords_point = Point(coords[1], coords[0])
        if zones is None:
            zones = self.getZonesPolygon()

        for zonaId, zona in zones.items():
            if coords_point.within(zona):
                return zonaId

        return 0


    def getAvailableZones(self):
        """Return list of available delivery zones."""
        return self.getZones().filter(isAvailable=True)


# ==================================================
    

    def getMinOrderForZona(self, zona_id) -> int:

        default = 700

        try:
            zones = self.getAvailableZones()
            zona = zones.get(number=zona_id)
            min_order = zona.order_price
        except Exception:
            return default
        
        return min_order


    def IsZonaAvailable(self, zona_id) -> bool:
        try:
            zones_available = self.getAvailableZones()
            isAvailable = zones_available.get(number=zona_id)
        except zones_available.model.DoesNotExist:
            return False
        
        return True
    

# ==================================================


    def update_json(self):

        all_zones = self.getZones()
        zones_list = []

        for zona in all_zones:

            coords = []

            for crd in zona.coords.split('],'):
                crd = crd.replace("]", "").replace("[", "")
                crd = crd.split(",")
                coords.append((float(crd[0]), float(crd[1])))

            zones_list.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        coords
                    ],
                },
                "properties": {
                    "number": zona.number,
                    "available": zona.isAvailable
                }
            })

        _json = {
            "type": "FeatureCollection",
            "features": zones_list
        }

        filename = 'delivery_zones.geojson'
        file = open(_dir + '/js/delivery/geojson/' + filename, 'w')
        json.dump(_json, file)


# def unix_time(self, t):
#     t = int(t.timestamp())
#     return str(t)