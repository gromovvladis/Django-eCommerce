from decimal import Decimal
import json
import random
import typing
from django.conf import settings
import requests
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
            params=dict(format="json", apikey=yandex_key, geocode=address, sco="latlong", kind="house", results=1, lang="ru_RU"),
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


    def route(self, startpoint:list, waypoints: list, departure_time=None, mode="driving"):
        
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

        token_request = requests.get("https://api-maps.yandex.ru/2.1/?apikey=27bbbf17-40e2-4c01-a257-9b145870aa2a&lang=ru_RU", params=params, headers=headers)
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

        params = {
            "callback": "id_171990" + ''.join([str(random.randint(0, 9)) for _ in range(15)]),
            "token": token,
            "rll": waypoints,
            # "rll": "92.904378,56.050918~92.900632,56.04213", #peredelay
            "rtm": "atm",
            "results": "1",
        }

        response = requests.get("https://api-maps.yandex.ru/services/route/2.0/", params=params, headers=headers)

        if response.status_code == 200:
            got: dict[str, typing.Any] = response.json()["response"]
            return got
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
        sity: str = data[0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName']
        got = "%s, %s" % (adr, sity) 
        return got
    

    def routeTime(self, start_point, end_point):
        rote = self.route(start_point, end_point)
        time = rote.time
        return time


    def exact(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        try:
            data = geoObject["GeoObjectCollection"]["featureMember"][0]
        except Exception:
            return False
        
        return True


class GISMap:

    def geocode(self, address) -> dict[str, typing.Any]:


        params = {
            "key": gis_key, 
            "fields": "items.point"
        }

        if isinstance(address, list):
            params['lat'] = address[0]
            params['long'] = address[1]
        else:    
            params['q'] = address


        response = requests.get(
            "https://catalog.api.2gis.com/3.0/items/geocode/",
            params=params,
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



    def route(self, startpoint:list, waypoints: list, departure_time=None, mode="driving"):
        
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
            "apikey": gis_key,
        }

        token_request = requests.get("https://api-maps.yandex.ru/2.1/?apikey=27bbbf17-40e2-4c01-a257-9b145870aa2a&lang=ru_RU", params=params, headers=headers)
        content = str(token_request.content)

        _str = '"token":"'
        start_position = content.find(_str) + len(_str)
        substring = content[start_position:]
        _str = '","'
        end_position = substring.find(_str) 
        token = substring[:end_position]

        points = []
        points.append(",".join(map(str, startpoint)))

        for point in waypoints:
            points.append(",".join(map(str, point)))
        waypoints = "|".join(points)

        params = {
            "callback": "id_171990" + ''.join([str(random.randint(0, 9)) for _ in range(15)]),
            "token": token,
            "rll": "92.904378,56.050918~92.900632,56.04213", 
            "rtm": "atm",
            "results": "1",
        }

        response = requests.get("https://api-maps.yandex.ru/services/route/2.0/", params=params, headers=headers)

        if response.status_code == 200:
            got: dict[str, typing.Any] = response.json()["response"]
            return got
        else:
            return 0


    def coordinates(self, geoObject) -> tuple[Decimal, ...]:
        """Fetch coordinates (longitude, latitude) for passed address."""
        data = geoObject["GeoObjectCollection"]["featureMember"]

        if not data:
            return None

        coordinates: str = data[0]["GeoObject"]["Point"]["pos"]
        longitude, latitude = tuple(coordinates.split(" "))

        return Decimal(longitude), Decimal(latitude)


    def address(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        data = geoObject["GeoObjectCollection"]["featureMember"]

        if not data:
            return None

        adr: str = data[0]["GeoObject"]["name"]
        sity: str = data[0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName']
        got = "%s, %s" % (adr, sity) 
        return got
    

    def routeTime(self, start_point, end_point):
        rote = self.route(start_point, end_point)
        time = rote.time
        return time


    def exact(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        try:
            data = geoObject["GeoObjectCollection"]["featureMember"][0]
        except Exception:
            return False
        
        return True


class Map(YandexMap):
    pass
