import json
from django.conf import settings
from django.db import models

_dir = settings.STATIC_PRIVATE_ROOT

class AbstractDeliveryZona(models.Model):
    """
    Delivery zonas. Dublicate in json file.
    """

    number = models.PositiveIntegerField("Номер зоны доставки", unique=True)
    description = models.CharField("Описание", max_length=255, blank=True, null=True)
    order_price = models.PositiveIntegerField("Минимальная цена заказа", default=700)
    delivery_price = models.PositiveIntegerField("Стоимость доставки", default=0)
    coords = models.CharField(
        "Координаты", 
        max_length=1020, 
        help_text="Координаты в формате: [[55.730719,37.583146],[55.719093,37.677903]]"
        " Получить можно на сайте: http://mapinit.ru/coords/"
    )
    isAvailable = models.BooleanField("Доставка доступна", max_length=255)
    isHide = models.BooleanField("Убрать с карты", max_length=255)


    def __str__(self):
        return "Зона №%s - %s" % (self.number, self.description)


    class Meta:
        abstract = True
        verbose_name = "Зона доставки"
        verbose_name_plural = "Зоны доставки"

    # Saving

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_json() 

    @classmethod
    def update_json(cls):

        all_zones = cls.objects.all()
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

        file = open(_dir + '/js/delivery/geojson/delivery_zones.geojson', 'w')
        json.dump(_json, file)
