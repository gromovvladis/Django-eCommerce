from django.db import models
from oscar.core.loading import get_class

ZonesUtils = get_class("delivery.utils", "ZonesUtils")
zones_utils = ZonesUtils() 

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
        zones_utils.update_json() 
