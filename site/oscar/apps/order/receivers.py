import json
import datetime
from datetime import timedelta
from rest_framework.renderers import JSONRenderer

from django.conf import settings
from django.dispatch import receiver
from django.utils.timezone import now

from oscar.apps.order.serializers import OrderSerializer
from oscar.apps.order.signals import order_status_changed, order_placed
from oscar.apps.checkout.signals import post_checkout
from oscar.apps.order.tasks import update_paying_status_task
from oscar.apps.communication.tasks import (
    _send_site_notification_new_order_to_staff,
    _send_push_notification_new_order_to_staff,
    _send_telegram_message_new_order_to_staff,
)
from .tasks import _send_order_to_evotor


# pylint: disable=unused-argument
@receiver(order_placed)
def update_paying_status(sender, order, user, **kwargs):
    if (
        order.status == settings.OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS
        and settings.CELERY
    ):
        update_paying_status_task.apply_async(
            args=[order.number], eta=now() + timedelta(minutes=11)
        )


def active_order_created(sender, order, **kwargs):
    if order.status not in settings.ORDER_STATUS_SEND_TO_EVOTOR:
        return

    serializer = OrderSerializer(order)
    order_json = json.loads(JSONRenderer().render(serializer.data).decode("utf-8"))

    order_str = create_order_list(order)
    order_time = format_order_time(order.order_time)

    ctx = {
        "user": order.user.get_name_and_phone(),
        "user_id": order.user.id,
        "source": order.sources.first().source_type.name,
        "shipping_method": order.shipping_method,
        "order_time": order_time,
        "number": order.number,
        "total": int(order.total),
        "order": order_str,
        "order_id": order.id,
        "url": order.get_full_url(),
        "staff_url": order.get_staff_url(),
    }

    if settings.CELERY:
        _send_order_to_evotor.delay(order_json)
        _send_site_notification_new_order_to_staff.delay(ctx)
        _send_push_notification_new_order_to_staff.delay(ctx)
        _send_telegram_message_new_order_to_staff.delay(ctx)
    else:
        _send_order_to_evotor(order_json)
        _send_site_notification_new_order_to_staff(ctx)
        _send_push_notification_new_order_to_staff(ctx)
        _send_telegram_message_new_order_to_staff(ctx)


order_status_changed.connect(active_order_created)
post_checkout.connect(active_order_created)


# helpers


def create_order_list(order):
    """Создает строку с перечнем товаров"""
    return ", ".join(
        [
            (
                f"{line.product.get_name() if line.product else line.name} ({line.quantity})"
            )
            for line in order.lines.all()
        ]
    )


def format_order_time(order_time):
    """Форматирует время заказа"""
    if isinstance(order_time, datetime.date):
        return order_time.strftime("%d.%m.%Y %H:%M")
    return order_time
