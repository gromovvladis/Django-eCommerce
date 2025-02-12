from django_tables2 import A, Column, LinkColumn, TemplateColumn
from django.utils.translation import ngettext_lazy

from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")

ConditionalOffer = get_model("offer", "ConditionalOffer")


class ConditionalOfferTable(DashboardTable):
    image = LinkColumn(
        "dashboard:offer-detail",
        args=[A("pk")],
    )
    name = LinkColumn(
        "dashboard:offer-detail",
        args=[A("pk")],
    )
    offer_type = Column(
        verbose_name="Тип",
        orderable=True,
    )
    voucher_count = Column(
        verbose_name="Промокоды",
        orderable=True,
    )
    start_datetime = TemplateColumn(
        verbose_name="Дата начала",
        template_code='{{ record.date_updated|date:"d.m.y H:i"|default:"-" }}',
    )
    end_datetime = TemplateColumn(
        verbose_name="Дата окончания",
        template_code='{{ record.date_updated|date:"d.m.y H:i"|default:"-" }}',
    )
    priority = Column(
        verbose_name="Приоритет",
        orderable=True,
    )
    benefit = TemplateColumn(
        verbose_name="Стимул",
        template_code="{{ offer.benefit.description|safe }}",
    )
    condition = TemplateColumn(
        verbose_name="Условие",
        template_code="{{ offer.condition.description|safe }}",
    )
    is_available = TemplateColumn(
        verbose_name="Активен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("is_available"),
    )
    restrictions = TemplateColumn(
        verbose_name="Активен",
        template_name="oscar/dashboard/offer/offer_row_restrictions.html",
        order_by=("availability_restrictions"),
    )
    num_applications = Column(
        verbose_name="Активен",
        orderable=True,
    )
    total_discount = TemplateColumn(
        verbose_name="Активен",
        template_name="oscar/dashboard/offer/offer_row_total_discount.html",
        order_by=("total_discount"),
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/offer/offer_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-tags"
    caption = ngettext_lazy("%s Акция", "%s Акций")

    class Meta(DashboardTable.Meta):
        model = ConditionalOffer
        fields = (
            "image",
            "name",
            "offer_type",
        )
        sequence = (
            "name",
            "class_options",
            "class_attributes",
            "class_additionals",
            "num_products",
            "requires_shipping",
            "track_stock",
            "...",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых акций."
