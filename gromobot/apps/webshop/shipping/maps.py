import json
import typing
from decimal import Decimal
from typing import List

import requests
from django.conf import settings

from .exceptions import InvalidKey, UnexpectedResponse
from .utils import unix_time


class YandexMap:
    """Yandex geocoder API client.

    :Example:
        >>> from yandex_geocoder import Client
        >>> client = Client("your-api-key")

        >>> coordinates = client.coordinates("Москва Льва Толстого 16")
        >>> assert coordinates == (Decimal("37.587093"), Decimal("55.733969"))

        >>> address = client.address(Decimal("37.587093"), Decimal("55.733969"))
        >>> assert address == "Россия, Москва, улица Льва Толстого, 16"

    """

    BASE_URL = "https://geocode-maps.yandex.ru/1.x/"
    ROUTE_URL = "https://api-maps.yandex.ru/services/route/2.0/"

    def __init__(self, api_key=None):
        self.api_key = api_key or settings.YANDEX_API_KEY

    def _make_request(self, url: str, params: dict) -> dict:
        """Helper method to handle HTTP requests."""
        params.update({"apikey": self.api_key})
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            raise InvalidKey()
        else:
            raise UnexpectedResponse(
                f"status_code={response.status_code}, body={response.content!r}"
            )

    def route(
        self,
        startpoint: List[float],
        waypoints: List[List[float]],
        departure_time: int,
        mode: str = "driving",
    ) -> typing.Dict[str, typing.Any]:
        # Формируем строку с координатами
        points = [",".join(map(str, startpoint))]  # Начальная точка
        for point in waypoints:
            points.append(",".join(map(str, point)))  # Промежуточные точки
        waypoints = "|".join(points)

        params = dict(
            format="json",
            waypoints=waypoints,
            departure_time=departure_time,
            mode=mode,
        )

        return self._make_request(self.ROUTE_URL, params)

    def geocode(self, address: str) -> dict:
        """Get geocode information for the address."""
        params = {
            "format": "json",
            "geocode": address,
            "sco": "latlong",
            "kind": "house",
            "results": 1,
            "lang": "ru_RU",
        }
        return self._make_request(self.BASE_URL, params)

    def coordinates(self, geoObject) -> tuple:
        """Extract coordinates (longitude, latitude) from geoObject."""
        data = geoObject.get("GeoObjectCollection", {}).get("featureMember", [])
        if not data:
            return None
        coordinates = data[0]["GeoObject"]["Point"]["pos"]
        longitude, latitude = tuple(coordinates.split(" "))
        return Decimal(longitude), Decimal(latitude)

    def address(self, geoObject) -> str:
        """Extract address from geoObject."""
        data = geoObject.get("GeoObjectCollection", {}).get("featureMember", [])
        if not data:
            return None
        return data[0]["GeoObject"]["name"]

    def route_time(self, start_point, end_point) -> int:
        """Get the travel time between two points in minutes."""
        route = self.route(start_point, end_point)
        if route:
            return int(route["DurationInTraffic"].split(".")[0]) // 60
        return 60

    def exact(self, geoObject) -> bool:
        """Check if geoObject has valid data."""
        try:
            geoObject["GeoObjectCollection"]["featureMember"][0]
            return True
        except (IndexError, KeyError):
            return False


class GISMap:

    # ----------------------------------------------------------------
    # Request with the provided API key
    # ----------------------------------------------------------------

    GEOCODE_URL = "https://catalog.api.2gis.com/3.0/items/geocode"
    ROUTE_URL = "http://routing.api.2gis.com/routing/7.0.0/global"
    DIRECTIONS_URL = "https://routing.api.2gis.com/carrouting/6.0.0/global"
    PAIRS_DIRECTIONS_URL = "https://routing.api.2gis.com/get_pairs/1.0/"
    DIST_MATRIX_URL = "https://routing.api.2gis.com/get_dist_matrix"

    def __init__(self, api_key=None):
        self.api_key = api_key or settings.GIS_API_KEY

    def geocode(
        self,
        address: typing.Optional[str] = None,
        coords: typing.Optional[tuple[float, float]] = None,
    ) -> typing.Dict[str, typing.Any]:
        """Получить геокод для адреса или координат."""
        params = {
            "type": "building",
            "fields": "items.point,items.address",
        }
        if coords:
            params.update({"lat": coords[0], "lon": coords[1], "radius": 200})
        elif address:
            params["q"] = address
        else:
            raise ValueError("Необходимо указать либо адрес, либо координаты.")
        return self._send_request(self.GEOCODE_URL, params)

    def routing(
        self,
        points: list,
        departure_time: typing.Optional[str] = None,
        transport: str = "car",
    ) -> typing.Dict[str, typing.Any]:
        """Расчет маршрута для списка точек."""
        data = self._prepare_routing_data(points, departure_time, transport)
        return self._send_request(self.ROUTE_URL, {}, data, "post")

    def directions(
        self,
        startpoint: list,
        waypoints: list,
        departure_time: typing.Optional[str] = None,
    ) -> typing.Dict[str, typing.Any]:
        """Получение направлений для маршрута."""
        data = self._prepare_routing_data(
            [[startpoint] + waypoints], departure_time, "car"
        )
        return self._send_request(
            self.DIRECTIONS_URL, {"key": self.GIS_KEY}, data, "post"
        )

    def pairs_directions(
        self, points: list, departure_time: typing.Optional[str] = None
    ) -> typing.Dict[str, typing.Any]:
        """Получение маршрутов для пар точек."""
        data = self._prepare_routing_data(points, departure_time)
        return self._send_request(
            self.PAIRS_DIRECTIONS_URL, {"key": self.GIS_KEY}, data, "post"
        )

    def distance_matrix(
        self,
        points: list,
        sources: list,
        targets: list,
        departure_time=None,
        type="jam",
        mode="driving",
    ):
        """Получить матрицу расстояний между точками."""
        data = self._prepare_dist_matrix_data(
            points, sources, targets, departure_time, type, mode
        )
        return self._send_request(self.DIST_MATRIX_URL, {"version": 2.0}, data, "post")

    def _send_request(
        self, url: str, params: dict, data: dict = None, method: str = "get"
    ) -> typing.Dict[str, typing.Any]:
        """Отправка HTTP-запроса."""
        params.update({"key": self.api_key})
        try:
            if method == "get":
                response = requests.get(url, params=params)
            elif method == "post":
                response = requests.post(url, params=params, data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            raise UnexpectedResponse(f"HTTP error: {err}")
        except requests.exceptions.RequestException as err:
            raise UnexpectedResponse(f"Request error: {err}")
        except json.JSONDecodeError:
            raise UnexpectedResponse(f"Failed to decode JSON response from {url}")

    def _prepare_routing_data(
        self, points: list, departure_time: typing.Optional[str], transport: str = "car"
    ) -> dict:
        """Подготовить данные для маршрутизации."""
        data = {
            "traffic_mode": "jam",
            "output": "summary",
            "route_mode": "fastest",
            "alternative": 0,
            "transport": transport,
        }
        if departure_time:
            data["traffic_mode"] = "statistic"
            data["utc"] = unix_time(departure_time)
        data["points"] = [
            {"lon": lon, "lat": lat} for point in points for lon, lat in point
        ]
        return data

    def _prepare_dist_matrix_data(
        self,
        points: list,
        sources: list,
        targets: list,
        departure_time=None,
        type="jam",
        mode="driving",
    ) -> dict:
        """Подготовка данных для матрицы расстояний."""
        data = {
            "type": type,
            "mode": mode,
            "detailed": "false",
            "points": [{"lon": point[0], "lat": point[1]} for point in points],
            "sources": sources,
            "targets": targets,
        }
        if departure_time:
            data["type"] = "statistic"
            data["start_time"] = unix_time(departure_time)
        return data

    # ----------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------

    def coordinates(self, geoObject) -> tuple[Decimal, ...]:
        """Fetch coordinates (longitude, latitude) for passed address."""
        try:
            data = geoObject["result"]
            if not data:
                return None
            coordinates = data["items"][0]["point"]
            return coordinates["lon"], coordinates["lat"]
        except Exception:
            return None

    def address(self, geoObject) -> str:
        """Fetch address for the provided coordinates."""
        try:
            data = geoObject.get("result", {})
            if not data or not data.get("items"):
                return "Адрес не найден"
            address = data["items"][0].get("address_name") or data["items"][0].get(
                "name"
            )
            return address if address else "Адрес не найден"
        except Exception:
            return None

    def route_time(self, start_point, end_point):
        """Получить время маршрута между двумя точками."""
        try:
            directions = self.directions(start_point, end_point)
            rote = directions.get("result").pop()
            time = rote.get("total_duration") // 60
            return time
        except Exception:
            return 60

    def route_distance(self, start_point, end_point):
        try:
            directions = self.directions(start_point, end_point)
            rote = directions.get("result").pop()
            dist = rote.get("total_distance") // 60
            return dist
        except Exception:
            return 60

    def exact(self, geoObject) -> str:
        """Проверка, точно ли определены координаты для адреса."""
        try:
            geoObject["result"]["items"][0]
        except Exception:
            return False
        return True


class Map(GISMap):
    pass
