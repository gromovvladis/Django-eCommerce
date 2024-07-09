from decimal import Decimal
import typing
import requests
from .exceptions import *


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

    __slots__ = ("api_key",)

    api_key: str 

    def __init__(self, api_key):
        self.api_key = api_key

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
    #             apikey=self.api_key, 
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
            params=dict(format="json", apikey=self.api_key, geocode=address, sco="latlong", kind="house", results=1, lang="ru_RU"),
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


    def route(self, startpoint:list, waypoints: list, departure_time, mode="driving"):
        
        # departure_time = Math.floor(departure_time / 1000) + 30 * 60;
        return 1
    
        points = []
        points.append(",".join(map(str, startpoint)))

        for point in waypoints:
            points.append(",".join(map(str, point)))
        waypoints = "|".join(points)
    

        headers = {
            "Host": "api-maps.yandex.ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Cookie": "_yasc=LztmM0KcQSne3W5pEb0qwIHYAJ6zWQF25vOkEXR7vffeuxTaCV2FTtCE0slYoSDG5w==; i=DWtXj47ypmA9+Tm0pJ2N25wwcNC3fOvWg/jS0m2Y7v5RSYYAlBjHV7OA3VfFkkWDgZRyK0nUSjehH4qKIzP5c6Z8rHI=; yandexuid=7555425611718764094",
            "Sec-Fetch-Dest": "script",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "TE": "trailers",
        }

        params = {
            "callback": "id_171990574332834242485", # chto eto
            "lang": "ru_RU",
            "token": "021aff246b78bc9f3b2f9a65442f4f4a", # chto eto
            "rll": "92.904378 %2C 56.050918 ~ 92.936331 %2C 56.040546",
            "rtm": "atm",
            "results": "1",
            "apikey": self.api_key,
        }

        # 56.050918, 92.904378
        # callback=id_171990266371274149337
        # token=021aff246b78bc9f3b2f9a65442f4f4a

        # 92.93299438518065,56.06153368905355

        response = requests.get("https://api-maps.yandex.ru/services/route/2.0/", params=params, headers=headers)



        if response.status_code == 200:
            got: dict[str, typing.Any] = response.json()["response"]
            return got
        elif response.status_code == 403:
            raise InvalidKey()
        else:
            raise UnexpectedResponse(
                f"status_code={response.status_code}, body={response.content!r}"
            )


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
    

    def routeTime(self):
        return 50 


    def exact(self, geoObject) -> str:
        """Fetch address for passed coordinates."""
        try:
            data = geoObject["GeoObjectCollection"]["featureMember"][0]
        except Exception:
            return False
        
        return True
