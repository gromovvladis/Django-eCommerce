import datetime

from django.conf import settings

from oscar.apps.checkout.signals import post_payment
from oscar.apps.order.signals import order_status_changed
from .tasks import (
    _send_site_notification_new_order_to_customer,
    _send_site_notification_order_status_to_customer,
    _send_sms_notification_order_status_to_customer,
)


def notify_about_new_order(sender, view, **kwargs):
    order = kwargs["order"]
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
        _send_site_notification_new_order_to_customer.delay(ctx)
    else:
        _send_site_notification_new_order_to_customer(ctx)


post_payment.connect(notify_about_new_order)


def notify_customer_about_order_status(sender, order, **kwargs):
    if order.user:
        ctx = {
            "user_id": order.user.id,
            "phone": str(order.user.username),
            "number": order.number,
            "new_status": kwargs["new_status"],
            "shipping_method": order.shipping_method,
            "url": order.get_absolute_url(),
            "order_id": order.id,
        }

        if settings.CELERY:
            _send_site_notification_order_status_to_customer.delay(ctx)
            _send_sms_notification_order_status_to_customer.delay(ctx)
        else:
            _send_site_notification_order_status_to_customer(ctx)
            _send_sms_notification_order_status_to_customer(ctx)


order_status_changed.connect(notify_customer_about_order_status)


# helpers


def create_order_list(order):
    """Создает строку с перечнем товаров"""
    return ", ".join(
        [f"{line.product.get_name()} ({line.quantity})" for line in order.lines.all()]
    )


def format_order_time(order_time):
    """Форматирует время заказа"""
    if isinstance(order_time, datetime.date):
        return order_time.strftime("%d.%m.%Y %H:%M")
    return order_time
