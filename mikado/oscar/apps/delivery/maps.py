from decimal import Decimal
import json
import random
import typing
from django.conf import settings
import requests
from .utils import unix_time
from .exceptions import *

yandex_key = settings.YANDEX_API_KEY
gis_key = settings.GIS_API_KEY


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

    # time_unix = self.unix_time(datetime.datetime.now() + datetime.timedelta(minutes=order_minutes))
    # через матрицу маршрутов
    # def route(self, startpoint:list, waypoints: list, departure_time, mode="driving"):

    #     # departure_time = Math.floor(departure_time / 1000) + 30 * 60;

    #     points = []
    #     points.append(",".join(map(str, startpoint)))

    #     for point in waypoints:
    #         points.append(",".join(map(str, point)))
    #     waypoints = "|".join(points)

    #     response = requests.get(
    #         "https://api.routing.yandex.net/v2/route",
    #         params=dict(
    #             format="json",
    #             apikey=api_key,
    #             waypoints=waypoints,
    #             departure_time=departure_time,
    #             mode=mode
    #         ),
    #     )

    #     if response.status_code == 200:
    #         got: dict[str, typing.Any] = response.json()["response"]
    #         return got
    #     elif response.status_code == 403:
    #         raise InvalidKey()
    #     else:
    #         raise UnexpectedResponse(
    #             f"status_code={response.status_code}, body={response.content!r}"
    #         )

    def geocode(self, address: str) -> dict[str, typing.Any]:
        response = requests.get(
            "https://geocode-maps.yandex.ru/1.x/",
            params=dict(
                format="json",
                apikey=yandex_key,
                geocode=address,
                sco="latlong",
                kind="house",
                results=1,
                lang="ru_RU",
            ),
        )

        if response.status_code == 200:
            got: dict[str, typing.Any] = response.json()["response"]
            return got
        elif response.status_code == 403:
            raise InvalidKey()
        else:
            raise UnexpectedResponse(
                f"status_code={response.status_code}, body={response.content!r}"
            )

    def route(
        self, startpoint: list, waypoints: list, departure_time=None, mode="driving"
    ):

        headers = {
            "Host": "api-maps.yandex.ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Cookie": "_yasc=y5NqUuF/v6ay8adpP06/7s8DHjLjyEbCAlsHVKB7CMSlYOnBc6SXpzxVCwKkxZw8lw==; i=DWtXj47ypmA9+Tm0pJ2N25wwcNC3fOvWg/jS0m2Y7v5RSYYAlBjHV7OA3VfFkkWDgZRyK0nUSjehH4qKIzP5c6Z8rHI=; yandexuid=7555425611718764094; yashr=8529745071719911678; receive-cookie-deprecation=1",
            "Sec-Fetch-Dest": "script",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "TE": "trailers",
        }

        params = {
            "lang": "ru_RU",
            "apikey": yandex_key,
        }

        token_request = requests.get(
            "https://api-maps.yandex.ru/2.1/?apikey=27bbbf17-40e2-4c01-a257-9b145870aa2a&lang=ru_RU",
            params=params,
            headers=headers,
        )
        content = str(token_request.content)

        _str = '"token":"'
        start_position = content.find(_str) + len(_str)
        substring = content[start_position:]
        _str = '","'
        end_position = substring.find(_str)
        token = substring[:end_position]

        points = []
        points.append(",".join(map(str, reversed(startpoint))))

        for pnt in waypoints:
            points.append(",".join(map(str, reversed(pnt))))
        waypoints = "~".join(points)

        params.update(
            {
                "callback": "id_171990"
                + "".join([str(random.randint(0, 9)) for _ in range(15)]),
                "token": token,
                "rll": waypoints,
                "rtm": "atm",
                "results": "1",
            }
        )

        response = requests.get(
            "https://api-maps.yandex.ru/services/route/2.0/",
            params=params,
            headers=headers,
        )

        fields = ["Distance", "DurationInTraffic"]
        res = {}

        content = str(response.content)

        for field in fields:
            start_position = content.find(field) + len(field) + 11
            substring = content[start_position:]
            _str = ","
            end_position = substring.find(_str)
            res[field] = substring[:end_position]

        if response.status_code == 200:
            return res
        else:
            return 0

    def coordinates(self, geoObject) -> tuple[Decimal, ...]:
        """Fetch coordinates (longitude, latitude) for passed address."""
        data = geoObject["GeoObjectCollection"]["featureMember"]

        if not data:
            return None

        coordinates: str = data[0]["GeoObject"]["Point"]["pos"]
        longitude, latitude = tuple(coordinates.split(" "))

        # return Decimal(latitude), Decimal(longitude)
        return Decimal(longitude), Decimal(latitude)

    def address(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        data = geoObject["GeoObjectCollection"]["featureMember"]

        if not data:
            return None

        # got: str = data[0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
        adr: str = data[0]["GeoObject"]["name"]
        # sity: str = data[0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName']
        # got = "%s, %s" % (adr, sity)
        # return got
        return adr

    def routeTime(self, start_point, end_point):
        rote = self.route(start_point, end_point)
        if rote:
            return int(rote["DurationInTraffic"].split(".")[0]) // 60
        return 60

    def exact(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        try:
            data = geoObject["GeoObjectCollection"]["featureMember"][0]
        except Exception:
            return False

        return True


class GISMap:

    # ----------------------------------------------------------------
    # Request with the provided API key
    # ----------------------------------------------------------------

    def geocode(self, address=None, coords=None) -> dict[str, typing.Any]:
        
        url = "https://catalog.api.2gis.com/3.0/items/geocode"

        params = {
            "key": gis_key,
            "type": "building",
            "fields": "items.point,items.address",
            "search_nearby": "true",
            "viewpoint1": "92.6406,56.1206",
            "viewpoint2": "93.2584,55.9460",
            # "page_size": 1,
            # "point": "92.8787,56.0083",
            # "radius": 10000,
            # "city_id":
        }

        if coords: 
            params["lat"] = coords[0]
            params["lon"] = coords[1]
            params["radius"] = 200
        elif address:
            params["q"] = address
        else: 
            return {"error": "Coordinates or address must be provided"}

        response = requests.get(url=url, params=params)

        if response.status_code == 200:
            return json.loads(response.content.decode('utf8'))
        elif response.status_code == 403:
            raise InvalidKey()
        else:
            raise UnexpectedResponse(
                f"status_code={response.status_code}, body={response.content!r}"
            )

    def routing(self, points: list, departure_time=None, transport="car"):
        """ Формат points: [[[lon,lat], [lon,lat]], [[lon,lat], [lon,lat]]], 
        Для каждого маршрута необходимо указать четное количество точек
        формат departure_time: 'YYYY-MM-DD HH:MM'"""

        url = "http://routing.api.2gis.com/routing/7.0.0/global"

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

        point_list = []

        for rote in points:
            point_list.append([
                {
                    "lon": rote[0][0],
                    "lat": rote[0][1],
                },
                {
                    "lon": rote[1][0],
                    "lat": rote[1][1],
                }
            ])

        data["points"] = point_list

        response = requests.post(url=url, params={"key": gis_key}, data=json.dumps(data))

        if response.status_code == 200:
            return json.loads(response.content.decode('utf8'))

    def directions(self, startpoint: list, waypoints: list, departure_time=None):
        """ Формат startpoint: [x,y], формат waypoints: [[x,y],[x,y],[x,y]], 
        формат departure_time: 'YYYY-MM-DD HH:MM'"""

        url = "https://routing.api.2gis.com/carrouting/6.0.0/global"

        data = {
            "type": "jam",
            "alternative": 0,
        }

        if departure_time:
            data["type"] = "statistic"
            data["utc"] = unix_time(departure_time)

        point_list = [{"y": startpoint[0], "x": startpoint[1], "start": True}]

        for waypoint in waypoints:
            point_list.append({"y": waypoint[0], "x": waypoint[1]})

        data["points"] = point_list

        response = requests.post(url=url, params={"key": gis_key}, data=json.dumps(data))

        if response.status_code == 200:
            return json.loads(response.content.decode('utf8'))

    def pairsDirections(self, points: list, departure_time=None, routing_type="car"):
        """ Формат points: [[[lon1,lat1],[lon1,lat2]],[[lon1,lat1],[lon1,lat2]]], 
        формат departure_time: 'YYYY-MM-DD HH:MM' """

        url = "https://routing.api.2gis.com/get_pairs/1.0/"

        data = {
            "type": "jam",
            "output": "simple",
        }

        if departure_time:
            data["type"] = "statistic"
            data["utc"] = unix_time(departure_time)

        point_list = []

        for rote in points:
            point_list.append({
                "lon1": rote[0][0],
                "lat1": rote[0][1],
                "lon2": rote[1][0], 
                "lat2": rote[1][1],
            })

        data["points"] = point_list

        response = requests.post(url=url, params={"key":gis_key, "routing_type":routing_type}, data=json.dumps(data))

        if response.status_code == 200:
            return json.loads(response.content.decode('utf8'))

    def distanceMatrix(self, points: list, sources: list, targets: list, departure_time=None, type="jam", mode="driving"):
        """ Формат points: [[lon,lat],[lon,lat],[lon,lat],[lon,lat]], 
        формат departure_time: 'YYYY-MM-DD HH:MM'
        формат sources (начальный точки): [0,1]
        формат targets (конечные точки): [2,3] """

        url = "https://routing.api.2gis.com/get_dist_matrix"

        data = {
            "type": type,
            "mode": mode,
            "detailed": "false",
        }

        if departure_time:
            data["type"] = "statistic"
            data["start_time"] = unix_time(departure_time)

        point_list = []

        for point in points:
            point_list.append({
                "lon": point[0],
                "lat": point[1],
            })

        data["points"] = point_list
        data["sources"] = sources
        data["targets"] = targets

        response = requests.post(url=url, params={"key":gis_key, "version":2.0}, data=json.dumps(data))

        if response.status_code == 200:
            return json.loads(response.content.decode('utf8'))

    # ----------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------

    def coordinates(self, geoObject) -> tuple[Decimal, ...]:
        """Fetch coordinates (longitude, latitude) for passed address."""
        data = geoObject["result"]

        if not data:
            return None
        data
        coordinates = data['items'][0]["point"]
        return coordinates['lon'], coordinates['lat']
    
    def address(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        data = geoObject["result"]

        if not data:
            return None
        
        adr = data['items'][0].get("address_name")
        
        if not adr:
            adr = data['items'][0].get("name")

        if not adr:
            adr = "Адрес не найден"
        return adr

    def routeTime(self, start_point, end_point):
        try:
            directions = self.directions(start_point, end_point)
            rote = directions.get('result').pop()
            time = rote.get('total_duration') // 60
            return time
        except Exception:
            return 60

    def routeDistance(self, start_point, end_point):
        try:
            directions = self.directions(start_point, end_point)
            rote = directions.get('result').pop()
            dist = rote.get('total_distance') // 60
            return dist
        except Exception:
            return 60

    def exact(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        try:
            data = geoObject["result"]['items'][0]
        except Exception:
            return False

        return True


class Map(GISMap):
    pass
