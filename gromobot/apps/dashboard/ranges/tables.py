from core.loading import get_class, get_model
from django.utils.translation import ngettext_lazy
from django_tables2 import Column, ManyToManyColumn, TemplateColumn

DashboardTable = get_class("dashboard.tables", "DashboardTable")

Range = get_model("offer", "Range")


class RangeTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="dashboard/ranges/range_list_row_name.html",
        order_by="name",
        attrs={
            "th": {"class": "name"},
        },
    )
    description = TemplateColumn(
        verbose_name="Описание",
        template_code='{{ record.description|default:"-"|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}',
        attrs={
            "th": {"class": "description"},
        },
    )
    num_products = TemplateColumn(
        verbose_name="Товары",
        template_name="dashboard/ranges/range_list_row_products.html",
        orderable=True,
        attrs={
            "th": {"class": "num_products"},
        },
    )
    included_categories = ManyToManyColumn(
        verbose_name="Категории",
        orderable=True,
        order_by="included_categories_count",
        attrs={
            "th": {"class": "num_products"},
        },
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="dashboard/table/boolean.html",
        order_by=("is_public"),
        attrs={
            "th": {"class": "is_public"},
        },
    )
    benefits = TemplateColumn(
        verbose_name="Активные предложения",
        template_name="dashboard/table/boolean.html",
        orderable=True,
        attrs={
            "th": {"class": "benefits"},
        },
    )
    date_created = Column(
        verbose_name="Дата",
        order_by="date_created",
        attrs={
            "th": {"class": "date_created"},
        },
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="dashboard/ranges/range_list_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-layer-group"
    caption = ngettext_lazy("%s Ассортимент", "%s Ассортиментов")

    class Meta(DashboardTable.Meta):
        model = Range
        fields = (
            "name",
            "description",
            "num_products",
            "included_categories",
            "benefits",
            "is_public",
            "date_created",
        )
        sequence = (
            "name",
            "description",
            "num_products",
            "included_categories",
            "benefits",
            "is_public",
            "date_created",
            "...",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых ассортиментов"

    def order_num_products(self, queryset, is_descending):
        queryset = sorted(
            queryset, key=lambda range: range.num_products(), reverse=is_descending
        )

        self.data.data = queryset
        self.data._length = len(queryset)

        return queryset, True
