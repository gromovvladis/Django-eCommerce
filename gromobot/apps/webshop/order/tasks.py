import logging

from apps.evotor.api.komtet import EvotorKomtet
from celery import shared_task
from core.loading import get_model
from django.conf import settings

logger = logging.getLogger("apps.webshop.order")

Order = get_model("order", "Order")


@shared_task
def update_paying_status_task(order_number, *args, **kwargs):
    try:
        order = Order.objects.get(number=order_number)
        if order.status == settings.INITIAL_ONLINE_PAYMENT_ORDER_STATUS:
            order.set_status(settings.FAIL_ORDER_STATUS)
    except Exception as err:
        logger.error(
            "Ошибка при проверке статуса заказа 'Ожидает оплаты' через 11 минут %s", err
        )


# ================= Evotor =================
@shared_task
def _send_order_to_evotor(order_json: dict):
    try:
        EvotorKomtet().create_check(order_json)
    except Exception as e:
        logger.error(f"Ошибка отправки чека Komtet: {e}")
