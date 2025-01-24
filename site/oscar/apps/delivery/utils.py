from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from django.db.models import Sum, F
from django.conf import settings

from oscar.core.loading import get_model

Order = get_model("order", "Order")


def unix_time(t):
    t = int(t.timestamp())
    return str(t)


def kitchen_busy(store):
    timezone = ZoneInfo(settings.TIME_ZONE)
    current_time = datetime.now(tz=timezone)
    active_orders = (
        Order.objects.prefetch_related("lines", "lines__product")
        .filter(status__in=settings.ORDER_BUSY_STATUSES, store=store)
        .annotate(
            total_cooking_time=F("lines__product__cooking_time") * F("lines__quantity")
        )
        .order_by("order_time")
    )
    busy_periods = [
        (
            order.order_time.astimezone(timezone) - timedelta(minutes=order.total_cooking_time),
            order.order_time.astimezone(timezone),
        )
        for order in active_orders
        if order.order_time.astimezone(timezone) > current_time
    ]

    return busy_periods


def couriers_busy(store):
    pass


def pickup_now(basket):
    start_time = basket.store.start_worktime
    end_time = basket.store.end_worktime

    basket_lines = basket.lines.prefetch_related("product").all()
    order_minutes = basket_lines.annotate(
        total_cooking_time=F("product__cooking_time") * F("quantity")
    ).aggregate(cooking_time_sum=Sum("total_cooking_time"))["cooking_time_sum"]
    new_order_cooking_time = timedelta(minutes=order_minutes)  # Время приготовления нового заказа

    # Текущее время
    timezone = ZoneInfo(settings.TIME_ZONE)
    current_time = datetime.now(tz=timezone)

    # Добавляем рабочие границы текущего дня
    current_day_start = datetime.combine(current_time.date(), start_time, tzinfo=timezone)
    earliest_start_time = max(current_time, current_day_start)
    busy_periods = kitchen_busy(basket.store)

    new_order_time = None
    while new_order_time is None:
        # Определяем границы текущего рабочего дня
        work_day_start = datetime.combine(earliest_start_time.date(), start_time, tzinfo=timezone)
        work_day_end = datetime.combine(earliest_start_time.date(), end_time, tzinfo=timezone)

        # Если текущий день уже закончился, переход к следующему дню
        if earliest_start_time >= work_day_end:
            earliest_start_time = datetime.combine(
                earliest_start_time.date() + timedelta(days=1), start_time, tzinfo=timezone
            )
            continue

        # Фильтруем занятые периоды для текущего дня
        day_busy_periods = [
            (max(start, work_day_start), min(end, work_day_end))
            for start, end in busy_periods
            if start.date() == earliest_start_time.date() or end.date() == earliest_start_time.date()
        ]
        work_day_start_end = current_time if current_time > work_day_start else work_day_start
        day_busy_periods.append((work_day_start, work_day_start_end))  # Начало рабочего дня
        day_busy_periods.append((work_day_end, work_day_end))  # Конец рабочего дня
        day_busy_periods.sort(key=lambda x: x[0])

        # Проверяем свободные промежутки
        for i in range(len(day_busy_periods) - 1):
            current_end = day_busy_periods[i][1]
            next_start = day_busy_periods[i + 1][0]
            if current_end >= earliest_start_time and current_end + new_order_cooking_time <= next_start:
                new_order_time = current_end + new_order_cooking_time
                break

        # Переход на следующий день, если не нашли свободного времени
        earliest_start_time = datetime.combine(earliest_start_time.date() + timedelta(days=1), start_time, tzinfo=timezone)

    return new_order_time


def delivery_now(request):
    pass


def is_valid_order_time(order_time, shipping_method):
    return True