from django_tables2 import A, Column, LinkColumn, TemplateColumn
from django.utils.translation import ngettext_lazy

from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")

ConditionalOffer = get_model("offer", "ConditionalOffer")


class ConditionalOfferTable(DashboardTable):
    image = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/offers/offer_row_image.html",
        orderable=False,
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
        template_code='{{ record.start_datetime|date:"d.m.y H:i"|default:"-" }}',
    )
    end_datetime = TemplateColumn(
        verbose_name="Дата окончания",
        template_code='{{ record.end_datetime|date:"d.m.y H:i"|default:"-" }}',
    )
    priority = Column(
        verbose_name="Приоритет",
        orderable=True,
    )
    benefit = TemplateColumn(
        verbose_name="Стимул",
        template_code="{{ record.benefit.description|safe }}",
        attrs={
            "th": {"class": "benefit"},
        },
    )
    condition = TemplateColumn(
        verbose_name="Условие",
        template_code="{{ record.condition.description|safe }}",
        attrs={
            "th": {"class": "condition"},
        },
    )
    is_available = TemplateColumn(
        verbose_name="Активен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("is_available"),
    )
    restrictions = TemplateColumn(
        verbose_name="Ограничения",
        template_name="oscar/dashboard/offers/offer_row_restrictions.html",
        order_by=("availability_restrictions"),
        attrs={
            "th": {"class": "restrictions"},
        },
    )
    num_applications = Column(
        verbose_name="Количество применений",
        orderable=True,
    )
    total_discount = TemplateColumn(
        verbose_name="Суммарная скидка",
        template_name="oscar/dashboard/offers/offer_row_total_discount.html",
        order_by=("total_discount"),
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/offers/offer_row_actions.html",
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
            "start_datetime",
            "end_datetime",
            "num_applications",
            "benefit",
            "condition",
            "priority",
            "total_discount",
        )
        sequence = (
            "image",
            "name",
            "offer_type",
            "voucher_count",
            "start_datetime",
            "end_datetime",
            "priority",
            "benefit",
            "condition",
            "is_available",
            "restrictions",
            "num_applications",
            "total_discount",
            "...",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых акций."
