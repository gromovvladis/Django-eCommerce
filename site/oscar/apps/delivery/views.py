import json
from datetime import datetime, timedelta

from django import http
from django.db.models import Sum, F
from django.conf import settings
from django.utils.timezone import now

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication

from oscar.core.loading import get_class, get_model
from .maps import Map

DeliveryZona = get_model("delivery", "DeliveryZona")
ZonesUtils = get_class("delivery.zones", "ZonesUtils")
Order = get_model("order", "Order")

_dir = settings.STATIC_PRIVATE_ROOT


def pickup_now(basket):
    start_time = basket.store.start_worktime
    end_time = basket.store.end_worktime

    basket_lines = basket.lines.prefetch_related("product").all()
    order_minutes = basket_lines.annotate(
        total_cooking_time=F("product__cooking_time") * F("quantity")
    ).aggregate(cooking_time_sum=Sum("total_cooking_time"))["cooking_time_sum"]

    new_order_cooking_time = timedelta(minutes=order_minutes)  # Время приготовления нового заказа

    active_orders = (
        Order.objects.prefetch_related("lines", "lines__product")
        .filter(status__in=settings.ORDER_ACTIVE_STATUSES)
        .annotate(
            total_cooking_time=F("lines__product__cooking_time") * F("lines__quantity")
        )
        .order_by("order_time")
    )

    # Текущее время
    current_time = now()
    timezone = current_time.tzinfo
    busy_periods = [
        (
            order.order_time - timedelta(minutes=order.total_cooking_time),
            order.order_time,
        )
        for order in active_orders
        if order.order_time > current_time
    ]

    # Добавляем рабочие границы текущего дня
    current_day_start = datetime.combine(current_time.date(), start_time, tzinfo=timezone)
    busy_periods.append((current_day_start, current_day_start))  # Начало дня
    busy_periods.sort(key=lambda x: x[0])

    earliest_start_time = max(current_time, current_day_start)

    new_order_time = None
    while new_order_time is None:
        # Определяем границы текущего рабочего дня
        work_day_start = datetime.combine(earliest_start_time.date(), start_time, tzinfo=timezone)
        work_day_end = datetime.combine(earliest_start_time.date(), end_time, tzinfo=timezone)

        # Фильтруем занятые периоды для текущего дня
        day_busy_periods = [
            (max(start, work_day_start), min(end, work_day_end))
            for start, end in busy_periods
            if start.date() == earliest_start_time.date() or end.date() == earliest_start_time.date()
        ]
        day_busy_periods.append((work_day_start, work_day_start))  # Начало рабочего дня
        day_busy_periods.append((work_day_end, work_day_end))  # Конец рабочего дня
        day_busy_periods.sort(key=lambda x: x[0])

        # Проверяем свободные промежутки
        for i in range(len(day_busy_periods) - 1):
            current_end = day_busy_periods[i][1]
            next_start = day_busy_periods[i + 1][0]
            if current_end >= earliest_start_time and current_end + new_order_cooking_time <= next_start:
                new_order_time = current_end + new_order_cooking_time
                break

        # Переход на следующий день, если не нашли свободного времени
        earliest_start_time = datetime.combine(earliest_start_time.date() + timedelta(days=1), start_time, tzinfo=timezone)

    return new_order_time


def delivery_time(request):
    pass


class OrderNowView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    map = Map()

    def post(self, request, *args, **kwargs):

        shipping_method = request.POST.get("shipping_method")
        basket = request.basket

        if shipping_method == "zona-shipping":
            coords = request.POST.get("coords").split(",")
            address = request.POST.get("address")
            zona_id = request.POST.get("zonaId")
            result = self.delivery(coords, address, zona_id, basket)
        else:
            result = self.pickup(basket)

        return http.JsonResponse(result, status=200)

    def pickup(self, basket):    
        current_time = now()    
        new_order_time = pickup_now(basket)
        before_order = new_order_time - current_time

        if before_order < timedelta(hours=2):
            minutes = before_order.total_seconds() // 60
            delivery_time_text = f"Самовывоз через {int(minutes)} мин."
        elif new_order_time.date() == current_time.date():
            delivery_time_text = f"Самовывоз сегодня в {new_order_time.strftime('%H:%M')}"
        elif new_order_time.date() == (current_time + timedelta(days=1)).date():
            delivery_time_text = f"Самовывоз завтра в {new_order_time.strftime('%H:%M')}"
        else:
            delivery_time_text = f"Самовывоз {new_order_time.strftime('%d.%m.%Y в %H:%M')}"

        return {
            "timeUTC": new_order_time.isoformat(),
            "delivery_time_text": delivery_time_text,
        }

    def delivery(self, coords, address, zona_id, basket):
        if not address and not any(item.strip() != "" for item in coords):
            return {"error": "Укажите адрес"}

        if not coords:
            geoObject = self.geoobject(address=address)
            coords = self.coords(geoObject)

        if not address:
            geoObject = self.geoobject(coords=coords)
            address = self.address(geoObject)

        if not address or not any(item.strip() != "" for item in coords):
            return {"error": "Адрес не найден"}

        zones = ZonesUtils.available_zones()

        if not zona_id:
            zona_id = ZonesUtils.zona_id(coords, zones)

        if not zona_id or zona_id == "0":
            return {"error": "Адрес вне зоны доставки"}

        if not ZonesUtils.is_zona_available(zona_id, zones):
            return {
                "coords": coords,
                "address": address,
                "error": "Временно не доставляем",
                "delivery_time_text": "Доставка по данному адресу временно не осуществляется",  # Доставим через Х мин.
            }

        min_order = ZonesUtils.min_order_for_zona(zona_id, zones)

        if not self.is_working_time():
            return {
                "coords": coords,
                "address": address,
                "zonaId": zona_id,
                "order_minutes": "С 9:00",  # время выполнения заказов в минутах
                "min_order": min_order,
                "delivery_time_text": "Заказ возможен на отложенное время",
            }

        order_minutes = self.rote_time(coords, zona_id, basket)
        delivery_time_text = "Доставим через %s мин." % order_minutes
        time_utc = format(
            datetime.today() + timedelta(minutes=order_minutes),
            "%d.%m.%Y %H:%M",
        )

        return {
            "coords": coords,  # строка типа 56.34535,92.34536
            "address": address,  # Строкак типа Ленина 112, Красноярск
            "zonaId": zona_id,  # Номер зоны доставки для shipping charge
            "timeUTC": time_utc,  # время в дормате 11.04.2024 11:55 для времени заказа
            "order_minutes": "~ %s мин."
            % order_minutes,  # время выполнения заказов в минутах
            "min_order": min_order,  # сумма минимального заказа для разных зон
            "delivery_time_text": delivery_time_text,  # Доставим через Х мин.
        }

    # ===================
    #  Yandex / 2Gis Maps
    # ===================

    def geoobject(self, address=None, coords=None):
        """Получает геобъект по адресу или координатам"""
        geoObject = self.map.geocode(address, coords)
        return geoObject

    def coords(self, geoObject):
        """Получает координы обекта по геобъекту"""
        coordinates = self.map.coordinates(geoObject)
        return coordinates

    def address(self, geoObject):
        """Получает адрес по геобъекту"""
        address = self.map.address(geoObject)
        return address

    # ===================
    #  Timers
    # ===================

    def rote_time(self, coords, zona_id, basket):
        """Получает координы обекта, до которого нужно простроить маршрут.
        Маршрут строим от точки, которая будет задана в корзине у стокрекорд партнера
        Возвращает инфорамию о поездке (растояние, время)"""

        coock_time = self.coockingTime(basket)

        # if not rote_time:
        try:
            line = basket.lines.first()
            store = line.stockrecord.store
            store_address = store.addresses.first()
            start_point = [store_address.coords_long, store_address.coords_lat]
        except Exception:
            start_point = [56.050918, 92.904378]

        end_points = []
        end_points.append(coords)
        rote_time = self.map.routeTime(start_point, end_points)

        return rote_time + coock_time

    def coocking_time(self, basket):
        basket_lines = basket.lines.prefetch_related("product").all()
        order_minutes = basket_lines.annotate(
            total_cooking_time=F("product__cooking_time") * F("quantity")
        ).aggregate(cooking_time_sum=Sum("total_cooking_time"))["cooking_time_sum"]
        return timedelta(minutes=order_minutes)


class OrderLaterView(APIView):
    """
    Время доставки к определенному времени
    """
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    def get(self, request, *args, **kwargs):
        current_time = datetime.today()
        start_time = request.basket.store.start_worktime
        end_time = request.basket.store.end_worktime
        
        pickup_time = pickup_now(request.basket) + timedelta(hours=2)

        if pickup_time.hour > end_time.hour or pickup_time.hour < start_time.hour:
            pickup_time = datetime.combine(pickup_time.date() + timedelta(days=1), start_time)

        data = {
            "minHours": start_time.hour,
            "maxHours": end_time.hour,
            "minDate": format(
                pickup_time,
                "%Y-%m-%dT%H:%M",
            ),
            "maxDate": format(
                current_time.replace(minute=59, hour=22) + timedelta(days=14),
                "%Y-%m-%dT%H:%M",
            ),
        }
        return http.JsonResponse({"datapicker": data}, status=200)


class DeliveryZonesGeoJsonView(APIView):
    """
    Return the 'delivery all zones json'.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        json_file = json.loads(
            open(
                _dir + "/js/frontend/delivery/geojson/delivery_zones.geojson", "rb"
            ).read()
        )
        return http.JsonResponse(json_file, status=202)
