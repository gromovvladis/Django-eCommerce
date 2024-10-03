from decimal import Decimal as D
from django.db.models import Sum, Avg, Count

from asgiref.sync import sync_to_async

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

User = get_user_model()
Staff = get_model("user", "Staff")
Order = get_model("order", "Order")
Line = get_model("order", "Line")
Basket = get_model("basket", "Basket")


@sync_to_async
def get_report_message(start_period):
    orders = Order.objects.filter(date_placed__gt=start_period)
    users = User.objects.filter(date_joined__gt=start_period)
    if not orders.exists() and not users.exists():
        return "За указанный период заказы и пользователи не найдены."
    else:
        orders_count = orders.count()
        orders_lines = Line.objects.filter(order__in=orders).count()
        new_users = users.count()
        new_customers = users.filter(orders__isnull=False).count()
        open_baskets = Basket.objects.filter(status=Basket.OPEN, date_created__gt=start_period).count()
        total_revenue = orders.aggregate(Sum("total"))["total__sum"] or D("0.00")
        average_costs = orders.aggregate(Avg("total"))["total__avg"] or D("0.00")

        msg = (
            f"Количество заказов: <b>{orders_count}</b>\n"
            f"Количество позиций: <b>{orders_lines}</b>\n"
            f"Новых пользователей: <b>{new_users}</b>\n"
            f"Новых клиентов: <b>{new_customers}</b>\n"
            f"Всего создано корзин: <b>{open_baskets}</b>\n"
            f"Общий доход: <b>{int(total_revenue)} ₽</b>\n"
            f"Средняя стоимость заказа: <b>{int(average_costs)} ₽</b>"
        )
        
        return msg


@sync_to_async
def get_staffs_message():
    staffs = Staff.objects.all().prefetch_related('user')
    if not staffs.exists():
        return "Список персонала пуст."
    else:
        msg_list = []
        for staff in staffs:
            msg = (
                f"<b>{staff.get_full_name}</b>\n"
                f"Телефон: {staff.user.username}\n"
                f"Должность: {staff.get_job}\n"
                f"Уведомления: {next((description for key, description in Staff.NOTIF_CHOICES if key == staff.notif), "Уведомления не настроены")}"
            )

            msg_list.append(msg)
            
        return "\n\n".join(msg_list)


@sync_to_async
def get_customers_message():
    users = User.objects.all()
    if not users.exists():
        return "Список пользователей пуст."
    else:
        users_count = users.count()
        customers = users.filter(orders__isnull=False)
        customers_count = customers.count()
        customers_2orders = customers.annotate(order_count=Count('orders')).filter(order_count__gte=2).count()
        customers_5orders = customers.annotate(order_count=Count('orders')).filter(order_count__gte=5).count()
        open_customer_baskets = Basket.objects.filter(status=Basket.OPEN, owner__isnull=False).count()
        open_guest_baskets = Basket.objects.filter(status=Basket.OPEN, owner__isnull=True).count()

        order_msg = (
            f"Всего пользователей: <b>{users_count}</b>\n"
            f"Всего клиентов: <b>{customers_count}</b>\n"
            f"Клиенты с 2 и более заказами: <b>{customers_2orders}</b>\n"
            f"Клиенты с 5 и более заказами: <b>{customers_5orders}</b>\n"
            f"Открыто авторизованных корзин: <b>{open_customer_baskets}</b>\n"
            f"Открыто гостевых корзин: <b>{int(open_guest_baskets)}</b>\n"
        )
        
        return order_msg
