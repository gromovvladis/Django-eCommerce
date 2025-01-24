import logging
from celery import shared_task

from django.conf import settings
from oscar.core.loading import get_model

logger = logging.getLogger("oscar.order")

Order = get_model("order", "Order")

@shared_task
def paying_status(order_number, *args, **kwargs):
    try:
        order = Order.objects.get(number=order_number)
        if order.status == settings.OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS:
            order.set_status(settings.OSCAR_FAIL_ORDER_STATUS)
    except Exception as err:
        logger.error("Ошибка при проверке статуса заказа 'Ожидает оплаты' через 11 минут %s", err)
