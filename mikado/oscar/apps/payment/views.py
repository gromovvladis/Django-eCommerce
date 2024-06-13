import logging
from django import http
from oscar.core.loading import get_class, get_model

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

PaymentManager = get_class("payment.methods", "PaymentManager")
YoomoneyPayment = get_class("payment.methods", "Yoomoney")
Source = get_model("payment", "Source")

logger = logging.getLogger("oscar.payment")


class UpdatePayment(APIView):
    """
    First page of the checkout.  We prompt user to either sign in, or
    to proceed as a guest (where we still collect their email address).
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):

        try:
            pk = kwargs.get('pk')
            source = PaymentManager.get_last_source(pk)
            pay_id = source.payment_id
        except Exception as e:
            return http.JsonResponse({'error': 'pk not valid', "status": 400}, status=400)
        
        if pay_id:
            try:
                pay_code = source.reference
                payment_method = PaymentManager(pay_code).get_method()

                payment_api = payment_method.get_payment_api(pay_id)

                refund_id = source.refund_id
                refund_api = payment_method.get_refund_api(refund_id)

                status = payment_method.update(source, payment_api, refund_api)

            except Exception as e:
               return http.JsonResponse({'error': 'fail api payment', "status": 400}, status=400)

        return http.JsonResponse({'status': status}, status=200)


class YookassaPaymentStatus(APIView):
    """
    Gey status from yookassa.
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
    ]

    def post(self, request, *args, **kwargs):

        event_type = request.POST('event')
        trans_id = request.POST('object').get('id')
        source = Source.object.get(Q(payment_id=trans_id) | Q(refund_id=trans_id))
        
        if request.ip in self.IP and source:
            if "payment" in event_type:
                try:
                    payment_api = YoomoneyPayment.get_payment_api(trans_id)
                    YoomoneyPayment.update(
                        source=source, 
                        payment=payment_api,
                    )
                    return http.JsonResponse({'success': 'ok', "status": 200}, status=200)
                
                except Exception:
                    return http.JsonResponse({'error': 'fail', "status": 400}, status=400)
                
            elif "refund" in event_type and source:
                try:
                    refund_api = YoomoneyPayment.get_refund_api(trans_id)
                    YoomoneyPayment.update(
                        source=source, 
                        refund=refund_api,
                    )
                    return http.JsonResponse({'success': 'ok', "status": 200}, status=200)
                
                except Exception:
                    return http.JsonResponse({'error': 'fail', "status": 400}, status=400)
                
            else:
                logger.error(
                    "Транзакция не имеет тип refund или payment её статус: %s",
                    event_type
                )
                return http.JsonResponse({'error': 'fail', "status": 400}, status=400)
        else:
            logger.error(
                "Не удалось получить источник платежа или IP недопустимый. Источник:%s, IP: %s",
                event_type,
                request.ip
            )
            return http.JsonResponse({'error': 'fail', "status": 400}, status=400)