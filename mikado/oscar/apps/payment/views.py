import json
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

    IP = [
        '185.71.76.0/27',
        '185.71.77.0/27',
        '77.75.153.0/25',
        '77.75.156.11',
        '77.75.156.35',
        '77.75.154.128/25',
        '2a02:5180::/32',
        '127.0.0.1',
    ]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def post(self, request, *args, **kwargs):
        trans_id = ""
        try:
            event_json = json.loads(request.body)
            notification = WebhookNotification(event_json)

            event = notification.event
            trans_id = notification.object.id

            source = Source.objects.get(Q(payment_id=trans_id) | Q(refund_id=trans_id))
            
            request_ip = self.get_client_ip(request)

            if request_ip in self.IP and source:
                if "payment" in event:
                    try:
                        pay_code = source.reference
                        payment = PaymentManager(pay_code).get_method()
                        payment.update(
                            source=source, 
                            payment=notification.object,
                        )
                        return http.JsonResponse({'success': 'ok', "status": 200}, status=200)
                    
                    except Exception:
                        return http.JsonResponse({'error': 'fail', "status": 400}, status=400)
                    
                elif "refund" in event:
                    try:
                        pay_code = source.reference
                        payment = PaymentManager(pay_code).get_method()
                        payment.update(
                            source=source, 
                            refund=notification.object,
                        )
                        return http.JsonResponse({'success': 'ok', "status": 200}, status=200)
                    
                    except Exception:
                        return http.JsonResponse({'error': 'fail', "status": 400}, status=400)
                    
                else:
                    logger.error(
                        "Транзакция не имеет тип refund или payment её статус: %s",
                        event
                    )
                    return http.JsonResponse({'error': 'fail', "status": 400}, status=400)
            else:
                logger.error(
                    "Не удалось получить источник платежа или IP недопустимый. Источник:%s, IP: %s",
                    event,
                    request.ip
                )
                return http.JsonResponse({'error': 'fail', "status": 400}, status=400)
            
        except Exception:
            logger.error(
                "Ошибка при получении trans_id или source. trans_id: %s, IP: %s",
                trans_id,
                self.get_client_ip(request),
            )
            return http.JsonResponse({'error': 'fail', "status": 400}, status=400)