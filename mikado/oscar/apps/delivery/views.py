# pylint: disable=attribute-defined-outside-init
from .maps import Map

import datetime
import json
from django import http
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from oscar.core.loading import get_class, get_model

from django.conf import settings

from django import http
from django.views.generic import View

DeliveryZona = get_model("delivery", "DeliveryZona")
ZonesUtils = get_class("delivery.zones", "ZonesUtils")

_dir = settings.STATIC_PRIVATE_ROOT

class DeliveryNowView(APIView):

    permission_classes = [AllowAny]
    map = Map()
 
    def post(self, request, *args, **kwargs):
        
        shipping_method = request.POST.get('shipping_method')
        basket = request.basket

        if shipping_method == "zona-shipping":
            coords = request.POST.get('coords')
            address = request.POST.get('address')
            zona_id = request.POST.get('zonaId')
            rote_time = request.POST.get('roteTime')
            result = self.delivery(coords, address, zona_id, rote_time, basket)
        else: 
            result = self.pickup(basket)

        return http.JsonResponse(result, status=200)
    

    def pickup(self, basket):

        # нужна проверка рабочее ли время

        order_minutes = 50 # расчет времени потом сделаем

        time_utc = format(datetime.datetime.today() + datetime.timedelta(minutes=order_minutes),'%d.%m.%Y %H:%M')
        delivery_time_text = "Самовывоз через %s мин." % order_minutes

        return {
            "timeUTC": time_utc, # время в дормате 11.04.2024 11:55 для времени заказа
            "delivery_time_text": delivery_time_text, # Доставим через Х мин.
        }
    
    
    def delivery(self, coords, address, zona_id, rote_time, basket):

        if not coords:
            geoObject = self.getGeoobject(address=address)
            coords = self.getCoords(geoObject)

        if not address:
            geoObject = self.getGeoobject(coords=coords.split(","))
            address = self.getAddress(geoObject)

        if not address or not coords:
            return {"error": "Адрес не найден"}
        
        zones = ZonesUtils.getAvailableZones()

        if not zona_id:
            zona_id = ZonesUtils.getZonaId(coords.split(","), zones)

        if not zona_id or zona_id == "0":
            return {"error": "Адрес вне зоны доставки"}
            
        if not ZonesUtils.IsZonaAvailable(zona_id, zones):
            return {
                "coords": coords,
                "address": address,
                "error": "Временно не доствляем",
                "delivery_time_text": "Доставка по данному адресу временно не осуществляется", # Доставим через Х мин.
            }
        
        min_order = ZonesUtils.getMinOrderForZona(zona_id, zones)
      
        if not self.IsWorkingTime():
            return {
                "coords": coords,
                "address": address,
                "zonaId": zona_id,
                "order_minutes": "С 9:00", # время выполнения заказов в минутах
                "min_order": min_order,
                "delivery_time_text": "Заказ возможен на отложенное время",
            }

        order_minutes = self.deliveryTime(coords, zona_id, rote_time, basket)
        delivery_time_text = "Доставим через %s мин." % order_minutes
        time_utc = format(datetime.datetime.today() + datetime.timedelta(minutes=order_minutes),'%d.%m.%Y %H:%M')
        
        return {
            "coords": coords, # строка типа 56.34535,92.34536
            "address": address, # Строкак типа Ленина 112, Красноярск
            "zonaId": zona_id, # Номер зоны доставки для shipping charge
            "timeUTC": time_utc, # время в дормате 11.04.2024 11:55 для времени заказа
            "order_minutes": "~ %s мин." % order_minutes, # время выполнения заказов в минутах
            "min_order": min_order, # сумма минимального заказа для разных зон
            "delivery_time_text": delivery_time_text, # Доставим через Х мин.
        }


# ===================
#  Yandex / 2Gis Maps
# ===================

    def getGeoobject(self, address=None, coords=None):
        """Получает геобъект по адресу или координатам"""
        geoObject = self.map.geocode(address, coords)
        return geoObject


    def getCoords(self, geoObject):
        """Получает координы обекта по геобъекту"""
        coordinates = self.map.coordinates(geoObject)
        return coordinates


    def getAddress(self, geoObject):
        """Получает адрес по геобъекту"""
        address = self.map.address(geoObject)
        return address

# ===================
#  WOrk Time
# ===================    

    def IsWorkingTime(coords):
        """Проверяет работает ли магазин в данный момент"""
        return True

# ===================
#  Timers
# ===================

    def deliveryTime(self, coords, zona_id, rote_time, basket):
        """Получает координы обекта, до которого нужно простроить маршрут. 
        Маршрут строим от точки, которая будет задана в корзине у стокрекорд партнера 
        Возвращает инфорамию о поездке (растояние, время)"""

        coock_time = self.coockingTime(basket)

        # if not rote_time:
        try:
            line = basket.lines.first()
            partner = line.stockrecord.partner
            partner_address = partner.addresses.first()
            start_point = [partner_address.coords_long, partner_address.coords_lat]
        except Exception:
            start_point = [56.050918, 92.904378]
            
        end_points = []
        end_points.append(coords.split(','))
        rote_time = self.map.routeTime(start_point, end_points)


        return rote_time + coock_time


    def coockingTime(self, basket):
        return 50


class DeliveryLaterView(APIView):
    """
    Время доставки к определенному времени
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):

        time_now = datetime.datetime.today()
        hours_delta = 2

        if time_now.minute > 30:
            hours_delta = 3

        data = {
            'minHours': 10,
            'maxHours': 22,
            'minDate': format(time_now.replace(minute=0) + datetime.timedelta(hours=hours_delta),'%Y-%m-%dT%H:%M'),
            'maxDate': format(time_now.replace(minute=59, hour=22) + datetime.timedelta(days=14),'%Y-%m-%dT%H:%M')
        }
        return http.JsonResponse({"datapicker": data}, status = 200)
    

class DeliveryZonesGeoJsonView(APIView):
    """
    Return the 'delivery all zones json'.
    """

    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        json_file = json.loads(open(_dir + '/js/frontend/delivery/geojson/delivery_zones.geojson', 'rb').read())
        return http.JsonResponse(json_file, status=202)
