import json
import ipaddress
import logging

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from django import http
from django.db.models import Q

from oscar.core.loading import get_class, get_model

PaymentManager = get_class("payment.methods", "PaymentManager")
Yoomoney = get_class("payment.methods", "Yoomoney")

Source = get_model("payment", "Source")

logger = logging.getLogger("oscar.payment")


class CallbackKomtet(APIView):
    """
    Get status order from Komtet.
    """

    permission_classes = [AllowAny]

    IP_RANGES = [
        '185.71.76.0/27',
        '185.71.77.0/27',
        '77.75.153.0/25',
        '77.75.156.11',
        '77.75.156.35',
        '77.75.154.128/25',
        '2a02:5180::/32',
        '127.0.0.1',
    ]


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Преобразуем IP-диапазоны в объекты ipaddress для быстрого поиска
        self.allowed_ips = [ipaddress.ip_network(ip) for ip in self.IP_RANGES]


    def get_client_ip(self, request):
        """Получение IP-адреса клиента с учётом прокси."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


    def is_ip_allowed(self, ip):
        """Проверка, принадлежит ли IP к разрешённым диапазонам."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return any(ip_obj in network for network in self.allowed_ips)
        except ValueError:
            logger.error("Неверный IP-адрес: %s", ip)
            return False


    def post(self, request, *args, **kwargs):
        pass
