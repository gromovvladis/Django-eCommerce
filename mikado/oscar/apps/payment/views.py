import json
import ipaddress
import logging
from django import http
from oscar.core.loading import get_class, get_model

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from yookassa.domain.notification import WebhookNotification

PaymentManager = get_class("payment.methods", "PaymentManager")
Yoomoney = get_class("payment.methods", "Yoomoney")
Source = get_model("payment", "Source")

logger = logging.getLogger("oscar.payment")


class UpdatePayment(APIView):

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            sources = PaymentManager.get_sources(pk)
        except Exception as e:
            return http.JsonResponse({'error': 'sources not found', "status": 400}, status=400)
        
        status = None
        for source in sources:
            pay_id = source.payment_id
            if pay_id and pay_id == source.payment_id:
                try:
                    pay_code = source.reference
                    payment_method = PaymentManager(pay_code).get_method()

                    payment_api = payment_method.get_payment_api(pay_id)

                    refund_id = source.refund_id
                    refund_api = payment_method.get_refund_api(refund_id)

                    status = payment_method.update(source, payment_api, refund_api)

                except Exception as e:
                    return http.JsonResponse({'error': f'Failed API payment. Error: {e}', "status": 400}, status=400)

        if status is None:
            return http.JsonResponse({'error': 'No valid sources found', "status": 400}, status=400)

        return http.JsonResponse({'status': status}, status=200)


class YookassaPaymentHandler(APIView):
    """
    Get status from yookassa.
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
        try:
            request_ip = self.get_client_ip(request)
            if not self.is_ip_allowed(request_ip):
                logger.warning("Недопустимый IP: %s", request_ip)
                return http.JsonResponse({'error': 'ip error', "status": 400}, status=400)
        
            event_json = json.loads(request.body)
            notification = WebhookNotification(event_json)
            if not hasattr(notification, 'event') or not hasattr(notification.object, 'id'):
                logger.error("Недостаточно данных в уведомлении: %s", event_json)
                return http.JsonResponse({'error': 'invalid notification data', "status": 400}, status=400)

            event = notification.event
            trans_id = notification.object.id
            source = Source.objects.get(Q(payment_id=trans_id) | Q(refund_id=trans_id))

            if "payment" in event:
                pay_code = source.reference
                payment = PaymentManager(pay_code).get_method()
                payment.update(
                    source=source, 
                    payment=notification.object,
                )
            elif "refund" in event:
                pay_code = source.reference
                payment = PaymentManager(pay_code).get_method()
                payment.update(
                    source=source, 
                    refund=notification.object,
                )
            else:
                logger.error(
                    "Транзакция не имеет тип refund или payment её статус: %s",
                    event
                )
                return http.JsonResponse({'error': 'no refund | no payment', "status": 400}, status=400)
       
        except Source.DoesNotExist:
            logger.error("Источник не найден для trans_id: %s", trans_id)
        except Source.MultipleObjectsReturned:
            logger.error("Найдено несколько источников для trans_id: %s", trans_id)
        except json.JSONDecodeError as e:
            logger.error("Ошибка декодирования JSON: %s. Тело запроса: %s", e, request.body)
            return http.JsonResponse({'error': 'invalid JSON', "status": 400}, status=400)
        except KeyError as e:
            logger.error("Отсутствующий ключ в JSON: %s. Тело запроса: %s", e, request.body)
            return http.JsonResponse({'error': 'missing key', "status": 400}, status=400)
        except Exception as e:
            logger.exception("Неожиданная ошибка: %s. Тело запроса: %s", e, request.body)
            return http.JsonResponse({'error': 'server error', "status": 500}, status=500)
        
        return http.JsonResponse({'success': 'ok', "status": 200}, status=200)