from django_tables2 import A, LinkColumn, TemplateColumn
from django.utils.translation import ngettext_lazy

from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")

DeliveryZona = get_model("delivery", "DeliveryZona")


class DeliveryZonesTable(DashboardTable):

    id = LinkColumn(
        "dashboard:delivery-update-zona",
        verbose_name="№",
        args=[A("pk")],
        orderable=True,
        attrs={
            "th": {"class": "number"},
        },
    )
    name = LinkColumn(
        "dashboard:delivery-update-zona",
        args=[A("pk")],
        orderable=True,
        attrs={
            "th": {"class": "name"},
        },
    )
    delivery_price = TemplateColumn(
        verbose_name="Цена доставки",
        template_name="oscar/dashboard/delivery/deliveryzones_row_deliveryprice.html",
        orderable=True,
        attrs={
            "th": {"class": "price"},
        },
    )
    order_price = TemplateColumn(
        verbose_name="Минимальная сумма заказа",
        template_name="oscar/dashboard/delivery/deliveryzones_row_orderprice.html",
        orderable=True,
        attrs={
            "th": {"class": "price"},
        },
    )
    isAvailable = TemplateColumn(
        verbose_name="Доставка доступна",
        template_name="oscar/dashboard/table/boolean.html",
        orderable=True,
        attrs={
            "th": {"class": "is_public"},
        },
    )
    isHide = TemplateColumn(
        verbose_name="Скрыть на карте",
        template_name="oscar/dashboard/delivery/deliveryzones_row_ishide.html",
        orderable=True,
        attrs={
            "th": {"class": "is_hide"},
        },
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/delivery/deliveryzones_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-location-dot"
    caption = ngettext_lazy("%s Зона доставки", "%s Зон доставки")

    class Meta(DashboardTable.Meta):
        model = DeliveryZona
        fields = (
            "id",
            "name",
            "delivery_price",
            "order_price",
            "isAvailable",
            "isHide",
        )
        sequence = (
            "id",
            "name",
            "delivery_price",
            "order_price",
            "...",
            "isAvailable",
            "isHide",
            "actions",
        )

        empty_text = "Нет зон доставки"
