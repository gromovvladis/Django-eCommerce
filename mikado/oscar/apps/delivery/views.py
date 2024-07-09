# pylint: disable=attribute-defined-outside-init
from .yandex_map import YandexMap
from .utils import ZonesUtils

import datetime
import json
from django import http
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from oscar.core.loading import get_class, get_model

from django.conf import settings

from .yandex_map import YandexMap
from .utils import ZonesUtils

from django import http
from django.views.generic import View

api_key = settings.YANDEX_API_KEY
DeliveryZona = get_model("delivery", "DeliveryZona")


class DeliveryNowView(View):

    permission_classes = [AllowAny]
    yandex_map = YandexMap(api_key)
    zones_utils = ZonesUtils()
 
    def post(self, request, *args, **kwargs):
        
        shipping_method = request.POST.get('shipping_method')
        basket = request.basket

        if shipping_method == "zona-shipping":
            coords = request.POST.get('coords')
            address = request.POST.get('address')
            zona_id = request.POST.get('zonaId')
            result = self.delivery(coords, address, zona_id, basket)
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
    
    
    def delivery(self, coords, address, zona_id, basket):

        if not coords:
            geoObject = self.getGeoobject(address)
            coords = self.getCoords(geoObject)

        if not address:
            geoObject = self.getGeoobject(coords)
            address = self.getAddress(geoObject)

        if not address or not coords:
            return {"error": "Адрес не найден"}

        if zona_id is None:
            zona_id = self.getZonaId(coords)

        if zona_id == 0 or zona_id == "0":
            return {"error": "Адрес вне зоны доставки"}
            
        if not self.IsZonaAvailable(zona_id):
            return {
                "coords": coords,
                "address": address,
                "error": "Временно не доствляем",
                "delivery_time_text": "Доставка по данному адресу временно не осуществляется", # Доставим через Х мин.
            }
        

        min_order = self.getMinOrderForZona(zona_id)
      
        if not self.IsWorkingTime():
            return {
                "coords": coords,
                "address": address,
                "zonaId": zona_id,
                "order_minutes": "С 9:00", # время выполнения заказов в минутах
                "min_order": min_order,
                "delivery_time_text": "Заказ возможен на отложенное время",
            }

        order_minutes = self.deliveryTime(coords, zona_id, basket)
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
#  Yandex
# ===================

    def getGeoobject(self, addressInfo):
        """Получает геобъект по адресу или координатам"""
        geoObject = self.yandex_map.geocode(addressInfo)
        return geoObject


    def getCoords(self, geoObject):
        """Получает координы обекта по геобъекту"""
        coordinates = self.yandex_map.coordinates(geoObject)
        return coordinates


    def getAddress(self, geoObject):
        """Получает адрес по геобъекту"""
        address = self.yandex_map.address(geoObject)
        return address

# ===================
#  Delivery zones Utils
# ===================

    def getZonaId(self, coords):
        """Получает координы обекта, возвращает id зоны доставки, либо 0, если адрес вне зоны доставки"""
        return self.zones_utils.getZonaId(coords)
    

    def IsZonaAvailable(self, zona_id):
        """Проверяет достпуна ли доставка в эту зону в данный момент"""
        return self.zones_utils.IsZonaAvailable(zona_id)


    def getMinOrderForZona(self, zona_id):
        """Сумма минимального заказа для зоны доставки"""
        return self.zones_utils.getMinOrderForZona(zona_id)

# ===================
#  ???
# ===================    

    def IsWorkingTime(coords):
        """Проверяет работает ли магазин в данный момент"""
        return True

# ===================
#  ???
# ===================

    def deliveryTime(self, coords, zona_id, basket):
        """Получает координы обекта, до которого нужно простроить маршрут. 
        Маршрут строим от точки, которая будет задана в корзине у стокрекорд партнера 
        Возвращает инфорамию о поездке (растояние, время)"""
        return 50
        # roteTime = self.yandex_map.routeTime(coords, zona_id)
        # return roteTime


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
    dir = settings.STATIC_PRIVATE_ROOT

    def get(self, request, *args, **kwargs):
        filename = 'delivery_zones.geojson'
        json_file = json.loads(open(self.dir + '/js/delivery/geojson/' + filename, 'rb').read())
        return http.JsonResponse(json_file, status=202)


