from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from asgiref.sync import sync_to_async

from oscar.core.loading import get_model

Order = get_model("order", "Order")


async def get_period(period: str):
    start_period = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_period = timezone.now()

    if period == "месяц":
        start_period = start_period - timedelta(days=30)
    elif period == "неделю":
        start_period = start_period - timedelta(days=7)

    return start_period, end_period


@sync_to_async
def get_orders(start_period: timezone = None, only_active: bool = False):
    orders = (
        Order.objects.all()
        .select_related("basket", "store", "user")
        .prefetch_related("sources", "lines")
    )

    if start_period:
        orders = orders.filter(date_placed__gte=start_period)

    if only_active:
        active_statuses = settings.ORDER_ACTIVE_STATUSES
        orders = orders.filter(status__in=active_statuses)

    return orders


@sync_to_async
def orders_list(orders):
    if not orders.exists():
        return ("За указанный период заказы не найдены.",)
    else:
        msg_list = []
        for order in orders:
            order_lines = [
                f"{line.product.get_name()} ({line.quantity})"
                for line in order.lines.all()
            ]

            source = order.sources.last()
            source_name = source.source_type.name if source else "-----"
            order_user = order.user if order.user else "-----"

            order_msg = (
                f"<b><a href='{order.get_staff_url()}'>Заказ №{order.number}</a></b>\n"
                f"{', '.join(order_lines)}\n"
                f"Статус: {order.status}\n"
                f"Время заказа: {order.order_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"Пользователь: {order_user}\n"
                f"Оплата: {source_name}\n"
                f"Доставка: {order.shipping_method}\n"
                f"Сумма: {order.total} ₽"
            )

            msg_list.append(order_msg)

        return msg_list


async def get_orders_message(orders):
    return await orders_list(orders)


async def get_active_orders(orders):
    return await orders_list(orders)
