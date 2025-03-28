from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.loading import get_model
from django.conf import settings
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

Order = get_model("order", "Order")


def unix_time(t):
    t = int(t.timestamp())
    return str(t)


def couriers_busy(store):
    pass


def kitchen_busy(store):
    timezone = ZoneInfo(settings.TIME_ZONE)
    current_time = datetime.now(tz=timezone)
    active_orders = (
        Order.objects.filter(status__in=settings.ORDER_BUSY_STATUSES, store=store)
        .annotate(
            total_cooking_time=Sum(
                F("lines__quantity") * F("lines__product__cooking_time")
            )
        )
        .order_by("order_time")
    )
    busy_periods = [
        (
            order.order_time.astimezone(timezone)
            - timedelta(minutes=order.total_cooking_time or 10),
            order.order_time.astimezone(timezone),
        )
        for order in active_orders
        if order.order_time.astimezone(timezone) > current_time
    ]

    return busy_periods


def pickup_now(basket):
    start_time = basket.store.start_worktime
    end_time = basket.store.end_worktime

    order_minutes = (
        basket.lines.aggregate(
            cooking_time_sum=Sum(F("product__cooking_time") * F("quantity"))
        )["cooking_time_sum"]
        or 0
    )

    # Время приготовления нового заказа
    new_order_cooking_time = timedelta(minutes=order_minutes)

    # Текущее время
    timezone = ZoneInfo(settings.TIME_ZONE)
    current_time = datetime.now(tz=timezone)

    # Добавляем рабочие границы текущего дня
    current_day_start = datetime.combine(
        current_time.date(), start_time, tzinfo=timezone
    )

    earliest_start_time = max(current_time, current_day_start)
    busy_periods = kitchen_busy(basket.store)

    max_days_ahead = 7
    attempts = 0

    new_order_time = None
    while new_order_time is None and attempts < max_days_ahead:
        attempts += 1
        # Определяем границы текущего рабочего дня
        work_day_start = datetime.combine(
            earliest_start_time.date(), start_time, tzinfo=timezone
        )
        work_day_end = datetime.combine(
            earliest_start_time.date(), end_time, tzinfo=timezone
        )

        # Если текущий день уже закончился, переход к следующему дню
        if earliest_start_time >= work_day_end:
            earliest_start_time = datetime.combine(
                earliest_start_time.date() + timedelta(days=1),
                start_time,
                tzinfo=timezone,
            )
            continue

        # Фильтруем занятые периоды для текущего дня
        day_busy_periods = [
            (start, end)
            for start, end in busy_periods
            if start.date() == earliest_start_time.date()
            or end.date() == earliest_start_time.date()
        ]

        current_work_day_start = (
            current_time if current_time > work_day_start else work_day_start
        )

        if not day_busy_periods or not any(
            start == work_day_start for start, _ in day_busy_periods
        ):
            day_busy_periods.append((work_day_start, current_work_day_start))

        if not day_busy_periods or not any(
            end == work_day_end for end, _ in day_busy_periods
        ):
            day_busy_periods.append((work_day_end, work_day_end))

        day_busy_periods.sort(key=lambda x: x[0])

        # Проверяем свободные промежутки
        for i in range(len(day_busy_periods) - 1):
            current_end = day_busy_periods[i][1]
            next_start = day_busy_periods[i + 1][0]
            if (
                current_end >= earliest_start_time
                and current_end + new_order_cooking_time <= next_start
            ):
                new_order_time = current_end + new_order_cooking_time
                break

        # Переход на следующий день, если не нашли свободного времени
        earliest_start_time = datetime.combine(
            earliest_start_time.date() + timedelta(days=1), start_time, tzinfo=timezone
        )

    return new_order_time


def shipping_now(request):
    pass


def is_valid_order_time(order_time, shipping_method):
    return True


# def kitchen_busy(store):
#     timezone = ZoneInfo(settings.TIME_ZONE)
#     current_time = datetime.now(tz=timezone)

#     active_orders = (
#         Order.objects.filter(status__in=settings.ORDER_BUSY_STATUSES, store=store)
#         .annotate(
#             total_cooking_time=Coalesce(
#                 Sum(F("lines__quantity") * F("lines__product__cooking_time")),
#                 20,  # default value if NULL
#             )
#         )
#         .order_by("order_time")
#         .only("order_time")  # Оптимизация: выбираем только нужные поля
#     )

#     return [
#         (
#             order.order_time.astimezone(timezone)
#             - timedelta(minutes=order.total_cooking_time),
#             order.order_time.astimezone(timezone),
#         )
#         for order in active_orders
#         if order.order_time.astimezone(timezone) > current_time
#     ]


# def pickup_now(basket):
#     timezone = ZoneInfo(settings.TIME_ZONE)
#     current_time = datetime.now(tz=timezone)
#     store = basket.store

#     # 1. Вычисление времени приготовления
#     order_minutes = (
#         basket.lines.aggregate(
#             cooking_time_sum=Sum(F("product__cooking_time") * F("quantity"))
#         )["cooking_time_sum"]
#         or 0
#     )
#     new_order_cooking_time = timedelta(minutes=order_minutes)

#     # 2. Предварительная подготовка данных
#     start_time = store.start_worktime
#     end_time = store.end_worktime
#     current_day_start = datetime.combine(
#         current_time.date(), start_time, tzinfo=timezone
#     )
#     earliest_start_time = max(current_time, current_day_start)

#     # 3. Оптимизация получения занятых периодов
#     busy_periods = [
#         (start, end) for start, end in kitchen_busy(store) if end > current_time
#     ]

#     # 4. Основной цикл поиска времени
#     for day_offset in range(7):  # max_days_ahead = 7
#         work_day = current_time.date() + timedelta(days=day_offset)
#         work_day_start = datetime.combine(work_day, start_time, tzinfo=timezone)
#         work_day_end = datetime.combine(work_day, end_time, tzinfo=timezone)

#         if earliest_start_time >= work_day_end:
#             continue

#         # 5. Формируем периоды для текущего дня
#         day_periods = [
#             (max(start, work_day_start), min(end, work_day_end))
#             for start, end in busy_periods
#             if start.date() == work_day or end.date() == work_day
#         ]

#         # 6. Добавляем границы рабочего дня
#         if not day_periods or day_periods[0][0] > work_day_start:
#             day_periods.insert(0, (work_day_start, work_day_start))

#         day_periods.append((work_day_end, work_day_end))
#         day_periods.sort()

#         # 7. Поиск свободного окна
#         for i in range(len(day_periods) - 1):
#             current_end = day_periods[i][1]
#             next_start = day_periods[i + 1][0]

#             if (
#                 current_end >= earliest_start_time
#                 and current_end + new_order_cooking_time <= next_start
#             ):
#                 return current_end + new_order_cooking_time

#     return None
