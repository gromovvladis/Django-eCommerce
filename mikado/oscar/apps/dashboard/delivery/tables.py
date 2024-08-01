
from django_tables2 import A, Column, LinkColumn, TemplateColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
DeliveryZona = get_model("delivery", "DeliveryZona")
 

class DeliveryZonesTable(DashboardTable):
    
    number = LinkColumn("dashboard:delivery-update-zona", args=[A("pk")])
    name = LinkColumn("dashboard:delivery-update-zona", args=[A("pk")])

    delivery_price = TemplateColumn(
        verbose_name="Цена доставки",
        template_name="oscar/dashboard/delivery/deliveryzones_row_deliveryprice.html",
        # accessor="get_num_products",
        accessor=A("delivery_price"),
        order_by="delivery_price",
    )

    order_price = TemplateColumn(
        verbose_name="Минимальная цена заказа",
        template_name="oscar/dashboard/delivery/deliveryzones_row_orderprice.html",
        accessor=A("order_price"),
        order_by="order_price",
    )

    isAvailable = TemplateColumn(
        verbose_name="Доставка доступна",
        template_name="oscar/dashboard/delivery/deliveryzones_row_isavailable.html",
        accessor=A("isAvailable"),
        order_by="isAvailable",
    )

    isHide = TemplateColumn(
        verbose_name="Скрыть на карте",
        template_name="oscar/dashboard/delivery/deliveryzones_row_ishide.html",
        accessor=A("isHide"),
        orderable="isHide",
    )

    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/delivery/deliveryzones_row_actions.html",
        orderable=False,
    )

    icon = "fas fa-location-dot"
    caption = ngettext_lazy("%s Зона доставки", "%s Зон доставки")


    class Meta(DashboardTable.Meta):
        model = DeliveryZona
        fields = ("number", "name", "delivery_price", "order_price", "isAvailable", "isHide")
        sequence = ("number", "name", "delivery_price", "order_price", "...", "isAvailable", "isHide", "actions")

