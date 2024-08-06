from django.conf import settings
from django.utils.safestring import mark_safe
from django_tables2 import A, Column, LinkColumn, TemplateColumn, BooleanColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Option = get_model("catalogue", "Option")
Additional = get_model("catalogue", "Additional")


class ProductTable(DashboardTable):
    image = TemplateColumn(
        verbose_name='',
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
    )
    title = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/product_row_title.html",
        order_by="title",
        accessor=A("title"),
    )
    variants = TemplateColumn(
        verbose_name="Варианты",
        template_name="oscar/dashboard/catalogue/product_row_variants.html",
        orderable=False,
    )
    additionals = TemplateColumn(
        verbose_name="Доп. товары",
        template_name="oscar/dashboard/catalogue/product_row_additionals.html",
        orderable=False,
    )
    options = TemplateColumn(
        verbose_name="Опции",
        template_name="oscar/dashboard/catalogue/product_row_options.html",
        orderable=False,
    )
    categories = TemplateColumn(
        verbose_name="Категории",
        template_name="oscar/dashboard/catalogue/product_row_categories.html",
        accessor=A("categories"),
        order_by="categories__name",
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/catalogue/product_row_price.html",
        # accessor="get_low_price",
        order_by="title",
        orderable=True,
    )
    is_public = BooleanColumn(verbose_name="Доступен", accessor="is_public", order_by=("is_public"))
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/product_row_actions.html",
        orderable=False,
    )

    icon = "fas fa-chart-bar"

    class Meta(DashboardTable.Meta):
        model = Product
        fields = ("date_updated", "is_public")
        sequence = (
            "image",
            "title",
            "categories",
            "additionals",
            "options",
            "variants",
            "price",
            "...",
            "is_public",
            "date_updated",
            "actions",
        )
        order_by = "-date_updated"

    def order_price(self, queryset, is_descending):
        queryset = sorted(
            queryset,
            key=lambda product: product.get_low_price(),
            reverse=is_descending
        )

        self.data.data = queryset
        self.data._length = len(queryset)

        return queryset, True


class CategoryTable(DashboardTable):
    image = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/category_row_image.html",
        orderable=False,
    )
    name = LinkColumn("dashboard:catalogue-category-update", args=[A("pk")])
    description = TemplateColumn(
        template_code='{{ record.description|default:""|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}'
    )
    # mark_safe is needed because of
    # https://github.com/bradleyayers/django-tables2/issues/187
    num_children = LinkColumn(
        "dashboard:catalogue-category-detail-list",
        args=[A("pk")],
        verbose_name=mark_safe("Дочерние категории"),
        accessor="get_num_children",
        orderable=False,
    )
    num_products = TemplateColumn(
        verbose_name="Товары",
        template_name="oscar/dashboard/catalogue/category_row_products.html",
        accessor="get_num_products",
        order_by="product",
    )
    is_public = BooleanColumn(verbose_name="Доступна", accessor="is_public", order_by=("is_public"))
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/category_row_actions.html",
        orderable=False,
    )

    icon = "fas fa-layer-group"
    caption = ngettext_lazy("%s Категория", "%s Категорий")

    class Meta(DashboardTable.Meta):
        model = Category
        fields = ("image", "name", "description", "is_public")
        sequence = ("image", "name", "description", "...", "is_public", "actions")


class AttributeOptionGroupTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_name.html",
        order_by="name",
    )
    option_summary = TemplateColumn(
        verbose_name="Значения пераметра",
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_option_summary.html",
        orderable=False,
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_actions.html",
        orderable=False,
    )

    icon = "fas fa-paperclip"
    caption = ngettext_lazy("%s Группа параметров атрибута", "%s Групп параметров атрибутов")

    class Meta(DashboardTable.Meta):
        model = AttributeOptionGroup
        fields = ("name",)
        sequence = ("name", "option_summary", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE


class OptionTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/option_row_name.html",
        order_by="name",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/option_row_actions.html",
        orderable=False,
    )

    icon = "fas fa-paperclip"
    caption = ngettext_lazy("%s Опция", "%s Опций")

    class Meta(DashboardTable.Meta):
        model = Option
        fields = ("name", "type", "help_text", "order", "required")
        sequence = ("name", "type", "help_text", "order", "required", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE


class AdditionalTable(DashboardTable):
    img = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/additional_row_image.html",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/additional_row_name.html",
        order_by="name",
    )
    max_amount = Column(
        verbose_name="Максимум",
        order_by="max_amount",
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/catalogue/additional_row_price.html",
        order_by="price",
    )
    old_price = TemplateColumn(
        verbose_name="Цена без скидки",
        template_name="oscar/dashboard/catalogue/additional_row_old_price.html",
        order_by="old_price",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/additional_row_actions.html",
        orderable=False,
    )
    is_public = BooleanColumn(verbose_name="Доступен", accessor="is_public", order_by=("is_public"))

    icon = "fas fa-chart-bar" 
    caption = ngettext_lazy("%s Дополнительный товар","%s Дополнительных товара")

    class Meta(DashboardTable.Meta):
        model = Additional
        fields = ("img", "name", "price", "old_price", "weight", "max_amount", "is_public")
        sequence = ("img", "name", "price", "old_price", "weight", "max_amount", "is_public", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE