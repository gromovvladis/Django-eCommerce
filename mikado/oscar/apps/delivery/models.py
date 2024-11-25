from django.conf import settings

import json
from datetime import timedelta
from django.utils import timezone
from django.db import models

from oscar.core.compat import get_user_model
User = get_user_model()

_dir = settings.STATIC_PRIVATE_ROOT

# -------- Зона доставки ---------------

class DeliveryZona(models.Model):
    """
    Delivery zonas. Dublicate in json file.
    """
    name = models.CharField("Название", max_length=255, blank=True, null=True)
    order_price = models.PositiveIntegerField("Минимальная сумма заказа", default=700)
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
        permissions = (
            ("full_access", "Полный доступ к доставке"),
            ("read", "Просматривать доставки"),
            ("update_delivery", "Изменять доставки"),    
        )
        verbose_name = "Зона доставки"
        verbose_name_plural = "Зоны доставки"

    # Saving
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_json() 
            
    @classmethod
    def update_json(cls):
        all_zones = cls.objects.all()

        user_zones_list = []
        admin_zones_list = []

        # Вспомогательная функция для преобразования строк координат в список кортежей
        def parse_coords(coord_string):
            return [
                tuple(map(float, crd.replace("]", "").replace("[", "").split(",")))
                for crd in coord_string.split('],')
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
                "properties": properties
            }

        # Обработка каждой зоны
        for zona in all_zones:
            coords = parse_coords(zona.coords)

            # Создаем объекты зон для пользователей и администраторов
            if not zona.isHide:
                user_zones_list.append(create_feature(zona, coords))

            admin_zones_list.append(create_feature(zona, coords, is_admin=True))

        # Создаем JSON объекты
        user_json = {
            "type": "FeatureCollection",
            "features": user_zones_list
        }

        admin_json = {
            "type": "FeatureCollection",
            "features": admin_zones_list
        }

        # Оптимизированная запись файлов с использованием контекстного менеджера
        file_paths = {
            'user': _dir + '/js/frontend/delivery/geojson/delivery_zones.geojson',
            'admin': _dir + '/js/dashboard/delivery/geojson/delivery_zones.geojson'
        }

        with open(file_paths['user'], 'w') as user_file, open(file_paths['admin'], 'w') as admin_file:
            json.dump(user_json, user_file)
            json.dump(admin_json, admin_file)


# -------- Курьер и его смены ---------------

class Courier(models.Model):

    STATUS_CHOICES = [
        ('pedestrian', 'Пешеход'),
        ('driving', 'Автокурьер'),
    ]
        
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile = models.OneToOneField("user.Staff", on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=STATUS_CHOICES, default='driving')

    def __str__(self):
        return self.user.get_full_name()


    class Meta:
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"
        ordering = ['user', 'profile']
        unique_together = ('user', 'type')
        get_latest_by = 'user_username'


class CourierShift(models.Model):

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
        verbose_name = "Смена курьера"
        verbose_name_plural = "Смены курьера"
        ordering = ['-start_time']
        unique_together = ('courier','start_time')
        get_latest_by = 'end_time'

# -------- Заказы ---------------

class DeliveryOrder(models.Model):

    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, null=False, blank=False)
    pickup_time = models.DateTimeField()
    delivery_time = models.DateTimeField()
    store = models.ForeignKey('store.Store', on_delete=models.CASCADE, null=True, blank=True)
    courier = models.ForeignKey('delivery.Courier', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_id}"
    
    class Meta:
        verbose_name = "Заказ доставки"
        verbose_name_plural = "Заказы доставки"
        ordering = ['-delivery_time']
        index_together = ['pickup_time', 'delivery_time']
    

# -------- Поездки и манрщруты ---------------

class Trip(models.Model):

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
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"
        ordering = ['start_time']
        index_together = ['start_time', 'end_time']


class Route(models.Model):

    trips = models.ManyToManyField('delivery.Trip')
    courier = models.ForeignKey('delivery.Courier', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"Route for {self.courier.user.get_full_name()} on {self.start_time}"

    class Meta:
        verbose_name = "Маршрут курьера"
        verbose_name_plural = "Маршруты курьеров"
        ordering = ['start_time']
        index_together = ['start_time', 'end_time']

# -------- Сессия доставки ---------------

class DeliverySession(models.Model):
    
    orders = models.ManyToManyField('delivery.DeliveryOrder')
    couriers = models.ManyToManyField('delivery.Courier')
    stores = models.ManyToManyField('store.Store')
    
    date = models.DateField(default=timezone.now)
    open_time = models.DateTimeField(auto_now_add=True)
    close_time = models.DateTimeField()

    def __str__(self):
        return f"Торговая сессия - дата: {self.date}"
    
    class Meta:
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