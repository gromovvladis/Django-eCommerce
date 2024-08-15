from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django_tables2 import A, Column, LinkColumn, TemplateColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
Category = get_model("catalogue", "Category")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Option = get_model("catalogue", "Option")
Additional = get_model("catalogue", "Additional")


class ProductClassTable(DashboardTable):

    name = LinkColumn(
        "dashboard:catalogue-class-update", 
        args=[A("pk")], 
        attrs = {'th': {'class': 'name'},}
    )
    class_options = TemplateColumn(
        verbose_name="Опции",
        template_name="oscar/dashboard/catalogue/product_class_row_options.html",
        order_by="options",
        accessor=A("get_options"),
        attrs = {'th': {'class': 'class_options'},}
    )
    class_additionals = TemplateColumn(
        verbose_name="Дополнительные товары",
        template_name="oscar/dashboard/catalogue/product_class_row_additionals.html",
        order_by="class_additionals",
        accessor=A("get_additionals"),
        attrs = {'th': {'class': 'class_additionals'},}
    )
    num_products = Column(
        verbose_name="Продукты",
        order_by="products",
        accessor=A("num_products"),
        attrs = {'th': {'class': 'num_products'},}
    )
    requires_shipping = TemplateColumn(
        verbose_name="Доставка",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("requires_shipping"),
        attrs = {'th': {'class': 'delivery'},}
    )
    track_stock = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("track_stock"),
        attrs = {'th': {'class': 'stock'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/product_class_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-list"
    caption = ngettext_lazy("%s Тип продуков", "%s Типов продуков")

    class Meta(DashboardTable.Meta):
        model = ProductClass
        fields = (
            "name",
            "class_options",
            "class_additionals",
            "num_products",
            "requires_shipping",
            "track_stock",
        )
        sequence = (
            "name",
            "class_options",
            "class_additionals",
            "num_products",
            "requires_shipping",
            "track_stock",
            "actions",
        )
        order_by = "-name"
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых типов продуктов"


class ProductTable(DashboardTable):
    image = TemplateColumn(
        verbose_name='',
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
        attrs = {'th': {'class': 'image'},}
    )
    title = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/product_row_title.html",
        order_by="title",
        accessor=A("title"),
        attrs = {'th': {'class': 'title'},}
    )
    variants = TemplateColumn(
        verbose_name="Варианты",
        template_name="oscar/dashboard/catalogue/product_row_variants.html",
        orderable=False,
        attrs = {'th': {'class': 'variants'},}
    )
    additionals = TemplateColumn(
        verbose_name="Доп. товары",
        template_name="oscar/dashboard/catalogue/product_row_additionals.html",
        orderable=False,
        attrs = {'th': {'class': 'additionals'},}
    )
    options = TemplateColumn(
        verbose_name="Опции",
        template_name="oscar/dashboard/catalogue/product_row_options.html",
        orderable=False,
        attrs = {'th': {'class': 'options'},}
    )
    cooking_time = TemplateColumn(
        verbose_name="Время приготовления",
        template_name="oscar/dashboard/catalogue/product_row_time.html",
        orderable=True,
        attrs = {'th': {'class': 'cooking_time'},}
    )
    categories = TemplateColumn(
        verbose_name="Категории",
        template_name="oscar/dashboard/catalogue/product_row_categories.html",
        accessor=A("categories"),
        order_by="categories__name",
        attrs = {'th': {'class': 'categories'},}
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/catalogue/product_row_price.html",
        order_by="title",
        orderable=True,
        attrs = {'th': {'class': 'price'},}
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        accessor="is_public",
        order_by=("is_public"),
        attrs = {'th': {'class': 'is_public'},}
    )

    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/product_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )
    statistic = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/product_row_statistic.html",
        orderable=False,
        attrs = {'th': {'class': 'statistic'},}
    )

    date_updated = Column(
        attrs = {'th': {'class': 'date_updated'}}
    )

    icon = "fas fa-chart-bar"
    caption = ngettext_lazy("%s Продукт", "%s Продуктов")

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
            "cooking_time",
            "...",
            "is_public",
            "date_updated",
            "actions",
            "statistic",
        )
        order_by = "-date_updated"
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых продуктов"

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
        attrs = {'th': {'class': 'image'},}
    )
    name = LinkColumn("dashboard:catalogue-category-update", args=[A("pk")], attrs = {'th': {'class': 'name'},})
    description = TemplateColumn(
        template_code='{{ record.description|default:"-"|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}',
        attrs = {'th': {'class': 'description'},}
    )
    # mark_safe is needed because of
    # https://github.com/bradleyayers/django-tables2/issues/187
    num_children = LinkColumn(
        "dashboard:catalogue-category-detail-list",
        args=[A("pk")],
        verbose_name=mark_safe("Дочерние категории"),
        accessor="get_num_children",
        orderable=True,
        attrs = {'th': {'class': 'num_children'},}
    )
    num_products = TemplateColumn(
        verbose_name="Товары",
        template_name="oscar/dashboard/catalogue/category_row_products.html",
        accessor="get_num_products",
        order_by="product",
        attrs = {'th': {'class': 'num_products'},}
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        accessor="is_public",
        order_by=("is_public"),
        attrs = {'th': {'class': 'is_public'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/category_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    statistic = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/category_row_statistic.html",
        orderable=False,
        attrs = {'th': {'class': 'statistic'},}
    )

    icon = "fas fa-layer-group"
    caption = ngettext_lazy("%s Категория", "%s Категорий")

    class Meta(DashboardTable.Meta):
        model = Category
        fields = ("image", "name", "description", "is_public")
        sequence = ("image", "name", "description", "...", "is_public", "actions", "statistic")
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых категорий"


class AttributeOptionGroupTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    option_summary = TemplateColumn(
        verbose_name="Значения пераметра",
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_option_summary.html",
        orderable=False,
        attrs = {'th': {'class': 'option_summary'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-paperclip"
    caption = ngettext_lazy("%s Группа параметров атрибута", "%s Групп параметров атрибутов")

    class Meta(DashboardTable.Meta):
        model = AttributeOptionGroup
        fields = ("name",)
        sequence = ("name", "option_summary", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых групп параметров атрибута"


class OptionTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/option_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    type = Column(
        verbose_name="Тип опции",
        attrs = {'th': {'class': 'type'},}
    )
    help_text = Column(
        verbose_name="Описание",
        attrs = {'th': {'class': 'description'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/option_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    required = TemplateColumn(
        verbose_name="Обязательная опция",
        template_name="oscar/dashboard/table/boolean.html",
        accessor="required",
        order_by=("required"),
        attrs = {'th': {'class': 'required'},}
    ) 

    order = Column(
        attrs = {'th': {'class': 'order'}}
    )

    icon = "fas fa-paperclip"
    caption = ngettext_lazy("%s Опция", "%s Опций")

    class Meta(DashboardTable.Meta):
        model = Option
        fields = ("name", "type", "help_text", "order", "required")
        sequence = ("name", "type", "help_text", "order", "required", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых опций"


class AdditionalTable(DashboardTable):
    image = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/additional_row_image.html",
        orderable=False,
        attrs = {'th': {'class': 'image'},}
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/catalogue/additional_row_name.html",
        order_by="name",
         attrs = {'th': {'class': 'name'},}
    )
    max_amount = Column(
        verbose_name="Максимум",
        order_by="max_amount",
        attrs = {'th': {'class': 'max_amount'},},
    )
    weight = TemplateColumn(
        verbose_name="Вес",
        template_name="oscar/dashboard/catalogue/additional_row_weight.html",
        order_by="weight",
        attrs = {'th': {'class': 'weight'},},
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/catalogue/additional_row_price.html",
        order_by="price",
        attrs = {'th': {'class': 'price'},},
    )
    old_price = TemplateColumn(
        verbose_name="Цена без скидки",
        template_name="oscar/dashboard/catalogue/additional_row_old_price.html",
        order_by="old_price",
        attrs = {'th': {'class': 'old_price'},},
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/additional_row_actions.html",
        orderable=False,
         attrs = {'th': {'class': 'actions'},}
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("is_public"),
        attrs = {'th': {'class': 'is_public'},})

    icon = "fas fa-chart-bar" 
    caption = ngettext_lazy("%s Дополнительный товар","%s Дополнительных товара")

    class Meta(DashboardTable.Meta):
        model = Additional
        fields = ("image", "name", "price", "old_price", "weight", "max_amount", "is_public")
        sequence = ("image", "name", "price", "old_price", "weight", "max_amount", "is_public", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых дополнительных товаров"


class StockAlertTable(DashboardTable):

    name = TemplateColumn( 
        verbose_name="Продукт",
        template_name="oscar/dashboard/catalogue/stock_alert_row_name.html",
        orderable=False,
        attrs = {'th': {'class': 'name'},}
    )
    partner = TemplateColumn(
        verbose_name="Точка продажи",
        template_name="oscar/dashboard/catalogue/stock_alert_row_partner.html",
        orderable=False,
        attrs = {'th': {'class': 'partner'},}
    )
    threshold = Column(
        verbose_name="Границы запасов",
        order_by="threshold",
        attrs = {'th': {'class': 'threshold'},}
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
    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/catalogue/stock_alert_row_status.html",
        order_by="status",
        attrs = {'th': {'class': 'status'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/stock_alert_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-cubes-stacked"
    
    filter = {
        "url": reverse_lazy("dashboard:stock-alert-list"),
        "values": [
            ("", "Все"), 
            ("?status=Открыто", "Открытые"), 
            ("?status=Закрыто", "Закрытые"), 
        ]
    }
    
    caption = ngettext_lazy("%s Уведомление о наличии", "%s Уведомлений о наличии")

    class Meta(DashboardTable.Meta):
        model = ProductClass
        fields = (
            "name",
            "partner",
            "threshold",
            "is_public",
            "date_created",
            "status",
        )
        sequence = (
            "name",
            "partner",
            "threshold",
            "is_public",
            "date_created",
            "status",
            "actions",
        )
        order_by = "-name"
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет уведомлений о наличии"
