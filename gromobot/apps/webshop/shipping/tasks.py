import json
from celery import shared_task
from django.conf import settings
from core.loading import get_model

ShippingZona = get_model("shipping", "ShippingZona")

_dir = settings.STATIC_PRIVATE_ROOT


@shared_task
def update_shipping_zones_jsons_task():
    all_zones = ShippingZona.objects.all()

    user_zones_list = []
    admin_zones_list = []

    # Вспомогательная функция для преобразования строк координат в список кортежей
    def parse_coords(coord_string):
        return [
            tuple(map(float, crd.replace("]", "").replace("[", "").split(",")))
            for crd in coord_string.split("],")
        ]

    # Вспомогательная функция для создания JSON объектов зоны
    def create_feature(zona, coords, is_admin=False):
        properties = {
            "number": zona.id,
            "available": zona.isAvailable,
        }
        if is_admin:
            properties["hide"] = zona.isHide

        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords],
            },
            "properties": properties,
        }

    # Обработка каждой зоны
    for zona in all_zones:
        coords = parse_coords(zona.coords)

        # Создаем объекты зон для пользователей и администраторов
        if not zona.isHide:
            user_zones_list.append(create_feature(zona, coords))

        admin_zones_list.append(create_feature(zona, coords, is_admin=True))

    # Создаем JSON объекты
    user_json = {"type": "FeatureCollection", "features": user_zones_list}
    admin_json = {"type": "FeatureCollection", "features": admin_zones_list}

    # Оптимизированная запись файлов с использованием контекстного менеджера
    file_paths = {
        "user": _dir + "/js/webshop/shipping/geojson/shipping_zones.geojson",
        "admin": _dir + "/js/dashboard/shipping/geojson/shipping_zones.geojson",
    }

    with open(file_paths["user"], "w") as user_file, open(
        file_paths["admin"], "w"
    ) as admin_file:
        json.dump(user_json, user_file)
        json.dump(admin_json, admin_file)
