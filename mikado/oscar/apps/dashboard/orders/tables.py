from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django_tables2 import A, Column, LinkColumn, TemplateColumn, ManyToManyColumn
from django.db.models import Count

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Order = get_model("order", "Order")

class OrderTable(DashboardTable):

    checkbox = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/orders/order_row_checkbox.html",
        orderable=False,
        attrs = {'th': {'class': 'checkbox'},}
    )
    name = TemplateColumn(
        verbose_name="Заказ",
        template_name="oscar/dashboard/orders/order_row_name.html",
        order_by="number",
        attrs = {'th': {'class': 'name'},}
    )
    # num_products = Column(
    #     verbose_name="Позиции",
    #     orderable=True,
    #     attrs = {'th': {'class': 'num_products'},}
    # )
    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/orders/order_row_status.html",
        orderable=True,
        attrs = {'th': {'class': 'status'},}
    )
    user = TemplateColumn(
        verbose_name="Клиент",
        template_name="oscar/dashboard/orders/order_row_user.html",
        orderable=True,
        attrs = {'th': {'class': 'user'},}
    )
    delivery = TemplateColumn(
        verbose_name="Доставка",
        template_name="oscar/dashboard/orders/order_row_delivery.html",
        order_by="shipping_method",
        attrs = {'th': {'class': 'delivery'},}
    )
    payment = TemplateColumn(
        verbose_name="Оплата ",
        template_name="oscar/dashboard/orders/order_row_payment.html",
        order_by="payment",
        attrs = {'th': {'class': 'payment'},}
    )
    total = TemplateColumn(
        verbose_name="Сумма",
        template_name="oscar/dashboard/orders/order_row_total.html",
        orderable=True,
        attrs = {'th': {'class': 'total'},}
    )
    order_time = TemplateColumn(
        verbose_name="Время",
        template_name="oscar/dashboard/orders/order_row_time.html",
        orderable=True,
        attrs = {'th': {'class': 'order_time'},}
    )

    icon = "fas fa-shopping-cart"
    caption = ngettext_lazy("%s Заказ", "%s Заказов")

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
            # "num_products",
            "delivery",
            "payment",
            "order_time",
            "..."
            # "actions",
            # "view",
        )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых заказов"

