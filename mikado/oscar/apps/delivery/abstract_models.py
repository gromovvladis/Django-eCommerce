from django.conf import settings

import json
from datetime import timedelta
from django.utils import timezone
from django.db import models

from oscar.core.compat import get_user_model
User = get_user_model()

_dir = settings.STATIC_PRIVATE_ROOT

# -------- Зона доставки ---------------

class AbstractDeliveryZona(models.Model):
    """
    Delivery zonas. Dublicate in json file.
    """

    number = models.PositiveIntegerField("Номер зоны доставки", unique=True)
    name = models.CharField("Название", max_length=255, blank=True, null=True)
    order_price = models.PositiveIntegerField("Минимальная цена заказа", default=700)
    delivery_price = models.PositiveIntegerField("Стоимость доставки", default=0)
    coords = models.CharField(
        "Координаты", 
        max_length=1020, 
        help_text="Координаты в формате: [[55.730719,37.583146],[55.719093,37.677903]]"
        " Получить можно на сайте: http://mapinit.ru/coords/"
    )
    isAvailable = models.BooleanField("Доставка доступна", max_length=255, default=True)
    isHide = models.BooleanField("Убрать с карты", max_length=255, default=False)

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

# -------- Курьер и его смены ---------------

class AbstractCourier(models.Model):

    STATUS_CHOICES = [
        ('pedestrian', 'Пешеход'),
        ('driving', 'Автокурьер'),
    ]
        
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile = models.OneToOneField("user.Profile", on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=STATUS_CHOICES, default='driving')

    def __str__(self):
        return self.user.get_full_name()


    class Meta:
        abstract = True
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"
        ordering = ['user', 'profile']
        unique_together = ('user', 'type')
        get_latest_by = 'user_username'


class AbstractCourierShift(models.Model):

    courier = models.ForeignKey('delivery.Courier', on_delete=models.CASCADE)
    routes = models.ManyToManyField('delivery.Route')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    orders_completed = models.IntegerField(default=0)
    distance_traveled = models.FloatField(default=0.0)
    time_on_road = models.DurationField(default=timedelta())

    def __str__(self):
        return f"Shift for {self.courier.user.get_full_name()}"

    class Meta:
        abstract = True
        verbose_name = "Смена курьера"
        verbose_name_plural = "Смены курьера"
        ordering = ['-start_time']
        unique_together = ('courier','start_time')
        get_latest_by = 'end_time'

# -------- Заказы ---------------

class AbstractDeliveryOrder(models.Model):

    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, null=False, blank=False)
    pickup_time = models.DateTimeField()
    delivery_time = models.DateTimeField()
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, null=True, blank=True)
    courier = models.ForeignKey('delivery.Courier', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_id}"
    
    class Meta:
        abstract = True
        verbose_name = "Заказ доставки"
        verbose_name_plural = "Заказы доставки"
        ordering = ['-delivery_time']
        index_together = ['pickup_time', 'delivery_time']
    

# -------- Поездки и манрщруты ---------------

class AbstractTrip(models.Model):

    start_point_coords = models.CharField(max_length=255)  
    start_point_address = models.CharField(max_length=255)  
    start_zona_id = models.IntegerField()  
    
    end_point_coords = models.CharField(max_length=255)  
    end_point_address = models.CharField(max_length=255) 
    end_zona_id = models.IntegerField()  

    duration = models.DurationField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    distance = models.FloatField() 

    def __str__(self):
        return f"Trip from {self.start_point}"
    
    class Meta:
        abstract = True
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"
        ordering = ['start_time']
        index_together = ['start_time', 'end_time']


class AbstractRoute(models.Model):

    trips = models.ManyToManyField('delivery.Trip')
    courier = models.ForeignKey('delivery.Courier', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"Route for {self.courier.user.get_full_name()} on {self.start_time}"

    class Meta:
        abstract = True
        verbose_name = "Маршрут курьера"
        verbose_name_plural = "Маршруты курьеров"
        ordering = ['start_time']
        index_together = ['start_time', 'end_time']

# -------- Сессия доставки ---------------

class AbstractDeliverySession(models.Model):
    
    orders = models.ManyToManyField('delivery.DeliveryOrder')
    couriers = models.ManyToManyField('delivery.Courier')
    partners = models.ManyToManyField('partner.Partner')
    
    date = models.DateField(default=timezone.now)
    open_time = models.DateTimeField(auto_now_add=True)
    close_time = models.DateTimeField()

    def __str__(self):
        return f"Торговая сессия - дата: {self.date}"
    
    class Meta:
        abstract = True
        verbose_name = "Торговая сессия"
        verbose_name_plural = "Торговые сессии"
        ordering = ['-date']

    def get_current_session(self):
        current_date = timezone.now().date()
        return self.objects.get_or_create(current_date)
    
    def close_session(self): 
        if self.close_time:
            raise ValueError("Сессия уже закрыта")
        
        self.close_time = timezone.now()
        self.save()

    def add_order(self, order):
        order_date = order.pickup_time.date()
        if order_date == self.date:
            self.orders.add(order)
        else:
            session = self.objects.get_or_create(order_date)
            session.orders.add(order)

    def get_orders(self):
        return self.orders.all()