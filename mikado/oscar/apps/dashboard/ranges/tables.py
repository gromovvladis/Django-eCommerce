
from django_tables2 import A, Column, LinkColumn, TemplateColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Range = get_model("offer", "Range")

class RangeTable(DashboardTable):

    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/ranges/range_list_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    description = TemplateColumn(
        template_code='{{ record.description|default:"-"|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}',
        attrs = {'th': {'class': 'description'},}
    )
    products = TemplateColumn(
        verbose_name="Товары",
        template_name="oscar/dashboard/ranges/range_list_row_products.html",
        order_by="product",
        attrs = {'th': {'class': 'num_products'},}
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("is_public"),
        attrs = {'th': {'class': 'is_public'},}
    )
    date_created = Column(
        verbose_name="Дата",
        order_by="date_created",
        attrs = {'th': {'class': 'date_created'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/ranges/range_list_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-layer-group"
    caption = ngettext_lazy("%s Ассортимент", "%s Ассортиментов")

    class Meta(DashboardTable.Meta):
        model = Range
        fields = ("name", "description", "products", "is_public", "date_created")
        sequence = ("name", "description", "products", "date_created", "...", "actions")
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых ассортиментов"

