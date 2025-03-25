from core.loading import get_class, get_model
from django.utils.translation import ngettext_lazy
from django_tables2 import A, LinkColumn, TemplateColumn

DashboardTable = get_class("dashboard.tables", "DashboardTable")

ShippingZona = get_model("shipping", "ShippingZona")


class ShippingZonesTable(DashboardTable):
    id = LinkColumn(
        "dashboard:shipping-update-zona",
        verbose_name="№",
        args=[A("pk")],
        orderable=True,
        attrs={
            "th": {"class": "number"},
        },
    )
    name = LinkColumn(
        "dashboard:shipping-update-zona",
        args=[A("pk")],
        orderable=True,
        attrs={
            "th": {"class": "name"},
        },
    )
    shipping_price = TemplateColumn(
        verbose_name="Цена доставки",
        template_name="dashboard/shipping/shippingzones_row_shippingprice.html",
        orderable=True,
        attrs={
            "th": {"class": "price"},
        },
    )
    order_price = TemplateColumn(
        verbose_name="Минимальная сумма заказа",
        template_name="dashboard/shipping/shippingzones_row_orderprice.html",
        orderable=True,
        attrs={
            "th": {"class": "price"},
        },
    )
    isAvailable = TemplateColumn(
        verbose_name="Доставка доступна",
        template_name="dashboard/table/boolean.html",
        orderable=True,
        attrs={
            "th": {"class": "is_public"},
        },
    )
    isHide = TemplateColumn(
        verbose_name="Скрыть на карте",
        template_name="dashboard/shipping/shippingzones_row_ishide.html",
        orderable=True,
        attrs={
            "th": {"class": "is_hide"},
        },
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="dashboard/shipping/shippingzones_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-location-dot"
    caption = ngettext_lazy("%s Зона доставки", "%s Зон доставки")

    class Meta(DashboardTable.Meta):
        model = ShippingZona
        fields = (
            "id",
            "name",
            "shipping_price",
            "order_price",
            "isAvailable",
            "isHide",
        )
        sequence = (
            "id",
            "name",
            "shipping_price",
            "order_price",
            "...",
            "isAvailable",
            "isHide",
            "actions",
        )

        empty_text = "Нет зон доставки"
