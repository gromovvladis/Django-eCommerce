from core.loading import get_class, get_model
from django.urls import reverse_lazy
from django.utils.translation import ngettext_lazy
from django_tables2 import TemplateColumn

DashboardTable = get_class("dashboard.tables", "DashboardTable")

Order = get_model("order", "Order")


class OrderTable(DashboardTable):
    checkbox = TemplateColumn(
        verbose_name="",
        template_name="dashboard/orders/order_row_checkbox.html",
        orderable=False,
        attrs={
            "th": {"class": "checkbox"},
        },
    )
    name = TemplateColumn(
        verbose_name="Заказ",
        template_name="dashboard/orders/order_row_name.html",
        order_by="number",
        attrs={
            "th": {"class": "name"},
        },
    )
    status = TemplateColumn(
        verbose_name="Статус",
        template_name="dashboard/orders/order_row_status.html",
        orderable=True,
        attrs={
            "th": {"class": "status"},
        },
    )
    user = TemplateColumn(
        verbose_name="Клиент",
        template_name="dashboard/orders/order_row_user.html",
        orderable=True,
        attrs={
            "th": {"class": "user"},
        },
    )
    shipping = TemplateColumn(
        verbose_name="Доставка",
        template_name="dashboard/orders/order_row_shipping.html",
        order_by="shipping_method",
        attrs={
            "th": {"class": "shipping"},
        },
    )
    payment = TemplateColumn(
        verbose_name="Оплата ",
        template_name="dashboard/orders/order_row_payment.html",
        order_by="source",
        attrs={
            "th": {"class": "payment"},
        },
    )
    total = TemplateColumn(
        verbose_name="Сумма",
        template_name="dashboard/orders/order_row_total.html",
        orderable=True,
        attrs={
            "th": {"class": "total"},
        },
    )
    order_time = TemplateColumn(
        verbose_name="Время",
        template_name="dashboard/orders/order_row_time.html",
        order_by="order_time",
        attrs={
            "th": {"class": "order_time"},
        },
    )

    icon = "fas fa-shopping-cart"
    caption = ngettext_lazy("%s Заказ", "%s Заказов")
    filter = {
        "url": reverse_lazy("dashboard:order-list"),
        "values": [
            ("", "Все"),
            ("status=Ожидает+оплаты", "Ожидает оплаты"),
            ("status=Обрабатывается", "Обрабатывается"),
            ("status=Готовится", "Готовится"),
            ("status=Готов", "Готов"),
            ("status=Доставляется", "Доставляется"),
            ("status=Отменён", "Отменён"),
            ("status=Завершён", "Завершён"),
        ],
    }

    class Meta(DashboardTable.Meta):
        model = Order
        fields = (
            "name",
            "status",
            "user",
            "total",
            "order_time",
        )
        sequence = (
            "checkbox",
            "name",
            "status",
            "user",
            "total",
            "shipping",
            "payment",
            "order_time",
            "...",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        row_attrs = {"class": lambda record: "new-record" if not record.is_open else ""}
        order_by = "date_placed"
        empty_text = "Нет созданых заказов"
