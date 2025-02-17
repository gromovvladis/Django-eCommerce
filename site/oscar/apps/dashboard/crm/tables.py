from django_tables2 import A, Column, LinkColumn, TemplateColumn, ManyToManyColumn
from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model
from django.utils.safestring import mark_safe

DashboardTable = get_class("dashboard.tables", "DashboardTable")

Store = get_model("store", "Store")
Terminal = get_model("store", "Terminal")
Staff = get_model("user", "Staff")
Product = get_model("catalogue", "Product")
Additional = get_model("catalogue", "Additional")
Category = get_model("catalogue", "Category")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Option = get_model("catalogue", "Option")


class CRMStoreEvotorTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/stores/evotor_table/store_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/stores/evotor_table/store_row_name.html",
        order_by="name",
    )
    id = Column(
        verbose_name="Эвотор ID",
        order_by="id",
    )
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/crm/stores/evotor_table/store_row_address.html",
        order_by="address",
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/crm/stores/evotor_table/store_row_date.html",
        order_by="updated_at",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/stores/evotor_table/store_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Магазин Эвотор", "%s Магазинов Эвотор")

    class Meta(DashboardTable.Meta):
        model = Store
        fields = (
            "name",
            "id",
        )
        sequence = (
            "check",
            "name",
            "id",
            "address",
            "date_updated",
            "actions",
        )

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых точек продажи Эвотор."


class CRMStoreSiteTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/stores/site_table/store_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/stores/site_table/store_row_name.html",
        order_by="name",
    )
    work_time = TemplateColumn(
        verbose_name="Время работы",
        template_name="oscar/dashboard/stores/store_row_time.html",
        order_by="start_worktime",
        attrs={
            "th": {"class": "date"},
        },
    )
    staff = TemplateColumn(
        verbose_name="Персонал",
        template_name="oscar/dashboard/stores/store_row_staff.html",
        order_by="users",
    )
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/stores/store_row_address.html",
        order_by="address",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/stores/store_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Магазин", "%s Магазинов")

    class Meta(DashboardTable.Meta):
        model = Store
        fields = (
            "name",
            "work_time",
        )
        sequence = (
            "check",
            "name",
            "work_time",
            "staff",
            "address",
            "actions",
        )

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых точек продажи."


class CRMTerminalEvotorTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_name.html",
        order_by="name",
    )
    id = Column(
        verbose_name="Эвотор ID",
        order_by="id",
    )
    stores = TemplateColumn(
        verbose_name="Магазин",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_store.html",
        order_by="store_id",
    )
    model = Column(
        verbose_name="Модель",
        order_by="model",
    )
    imei = Column(
        verbose_name="IMEI",
        order_by="imei",
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_date.html",
        order_by="updated_at",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Терминал Эвотор", "%s Терминалы Эвотор")

    class Meta(DashboardTable.Meta):
        model = Terminal
        fields = (
            "name",
            "id",
            "model",
            "imei",
            "date_updated",
        )
        sequence = (
            "check",
            "name",
            "id",
            "stores",
            "model",
            "imei",
            "date_updated",
            "actions",
        )

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых терминалов Эвотор."


class CRMTerminalSiteTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/crm/terminals/site_table/terminal_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/terminals/site_table/terminal_row_name.html",
        order_by="name",
    )
    stores = TemplateColumn(
        verbose_name="Магазины",
        template_name="oscar/dashboard/stores/terminal_row_store.html",
        order_by="store",
    )
    model = Column(
        verbose_name="Модель",
        order_by="model",
    )
    imei = Column(
        verbose_name="IMEI",
        order_by="imei",
    )
    date_created = TemplateColumn(
        verbose_name="Создан",
        template_name="oscar/dashboard/stores/terminal_row_date_created.html",
        order_by="date_created",
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/stores/terminal_row_date_updated.html",
        order_by="date_updated",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/stores/terminal_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-tablet-screen-button"
    caption = ngettext_lazy("%s Терминал", "%s Терминалов")

    class Meta(DashboardTable.Meta):
        model = Terminal
        fields = (
            "name",
            "stores",
            "model",
            "imei",
            "date_created",
            "date_updated",
        )
        sequence = (
            "check",
            "name",
            "stores",
            "model",
            "imei",
            "date_created",
            "date_updated",
            "actions",
        )

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых терминалов."


class CRMStaffEvotorTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_name.html",
        order_by="name",
    )
    id = Column(
        verbose_name="Эвотор ID",
        order_by="id",
    )
    role = Column(
        verbose_name="Должность",
        order_by="role",
    )
    phone = Column(
        verbose_name="Пользователь",
        order_by="phone",
    )
    stores = TemplateColumn(
        verbose_name="Магазины",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_stores.html",
        order_by="stores",
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_date.html",
        order_by="updated_at",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-user-group"
    caption = ngettext_lazy("%s Сотрудник Эвотор", "%s Сотрудники Эвотор")

    class Meta(DashboardTable.Meta):
        model = Staff
        fields = (
            "name",
            "id",
        )
        sequence = (
            "check",
            "name",
            "id",
            "role",
            "phone",
            "stores",
            "date_updated",
            "actions",
        )

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых сотрудников Эвотор."


class CRMStaffSiteTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/crm/staffs/site_table/staff_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/staffs/site_table/staff_row_name.html",
        order_by="name",
    )
    role = TemplateColumn(
        verbose_name="Должность",
        template_name="oscar/dashboard/stores/staff_row_role.html",
        order_by="role",
    )
    user = TemplateColumn(
        verbose_name="Пользователь",
        template_name="oscar/dashboard/stores/staff_row_user.html",
        order_by="user",
    )
    stores = TemplateColumn(
        verbose_name="Магазины",
        template_name="oscar/dashboard/stores/staff_row_stores.html",
        order_by="stores",
    )
    notif = TemplateColumn(
        verbose_name="Уведомления",
        template_name="oscar/dashboard/stores/staff_row_notif.html",
        order_by="telegram",
    )
    age = Column(
        verbose_name="Возраст",
        order_by="age",
    )
    is_active = TemplateColumn(
        verbose_name="Активен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by="is_active",
        attrs={
            "th": {"class": "active"},
        },
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/stores/staff_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-id-card-clip"
    caption = ngettext_lazy("%s Сотрудник", "%s Сотрудников")

    class Meta(DashboardTable.Meta):
        model = Staff
        fields = (
            "check",
            "name",
            "role",
            "user",
            "stores",
            "notif",
            "age",
            "is_active",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Список сотрудников пуст."


# ===========================================


class CRMProductEvotorTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Товар",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_name.html",
        order_by="name",
    )
    description = TemplateColumn(
        verbose_name="Описание",
        template_code='{{ record.description|default:"-"|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}',
    )
    parent = TemplateColumn(
        verbose_name="Группа",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_group.html",
        order_by="parent",
    )
    stores = TemplateColumn(
        verbose_name="Магазин",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_store.html",
        order_by="store",
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_price.html",
        order_by="price",
    )
    tax = TemplateColumn(
        verbose_name="Налог",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_tax.html",
        order_by="tax",
    )
    measure_name = Column(
        verbose_name="Ед.изм.",
        order_by="measure_name",
        attrs={
            "th": {"class": "measure_name"},
        },
    )
    allow_to_sell = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by="allow_to_sell",
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_date.html",
        order_by="updated_at",
        attrs={
            "th": {"class": "date_updated"},
        },
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-cookie-bite"
    caption = ngettext_lazy("%s товар", "%s Продуктов")

    class Meta(DashboardTable.Meta):
        model = Product
        fields = (
            "check",
            "name",
            "description",
            "parent",
            "stores",
            "price",
            "tax",
            "measure_name",
            "allow_to_sell",
            "date_updated",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Список товаров пуст."


class CRMProductSiteTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/products/site_table/product_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    image = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/products/site_table/product_row_name.html",
        order_by="name",
        attrs={
            "th": {"class": "title"},
        },
    )
    variants = TemplateColumn(
        verbose_name="Варианты",
        template_name="oscar/dashboard/catalogue/product_row_variants.html",
        orderable=True,
    )
    additionals = TemplateColumn(
        verbose_name="Доп. товары",
        template_name="oscar/dashboard/catalogue/product_row_additionals.html",
        orderable=True,
        order_by="productadditional",
    )
    options = TemplateColumn(
        verbose_name="Опции",
        template_name="oscar/dashboard/catalogue/product_row_options.html",
        orderable=False,
    )
    cooking_time = TemplateColumn(
        verbose_name="Время приготовления",
        template_name="oscar/dashboard/catalogue/product_row_time.html",
        orderable=True,
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
        order_by="min_price",
        orderable=True,
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        accessor="is_public",
        order_by=("is_public"),
    )
    date_updated = TemplateColumn(
        template_code='{{ record.date_updated|date:"d.m.y H:i" }}',
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/product_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-chart-bar"
    caption = ngettext_lazy("%s товар", "%s Продуктов")

    class Meta(DashboardTable.Meta):
        model = Product
        fields = ("date_updated", "is_public")
        sequence = (
            "check",
            "image",
            "name",
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
        )
        order_by = "-date_updated"
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых товаров."


class CRMAdditionalEvotorTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/crm/additionals/evotor_table/additional_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/additionals/evotor_table/additional_row_name.html",
        order_by="name",
    )
    description = TemplateColumn(
        verbose_name="Описание",
        template_code='{{ record.description|default:"-"|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}',
    )
    stores = TemplateColumn(
        verbose_name="Магазин",
        template_name="oscar/dashboard/crm/additionals/evotor_table/additional_row_store.html",
        order_by="store",
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/crm/additionals/evotor_table/additional_row_price.html",
        order_by="price",
    )
    tax = Column(
        verbose_name="Налог",
        order_by="tax",
    )
    measure_name = Column(
        verbose_name="Ед.изм.",
        order_by="measure_name",
    )
    allow_to_sell = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by="allow_to_sell",
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/crm/additionals/evotor_table/additional_row_date.html",
        order_by="updated_at",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/additionals/evotor_table/additional_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-cookie-bite"
    caption = ngettext_lazy("%s товар", "%s Продуктов")

    class Meta(DashboardTable.Meta):
        model = Product
        fields = (
            "check",
            "name",
            "description",
            "stores",
            "price",
            "tax",
            "measure_name",
            "allow_to_sell",
            "date_updated",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Список товаров пуст."


class CRMAdditionalSiteTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/additionals/site_table/additional_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    image = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/additionals/site_table/additional_row_name.html",
        order_by="name",
        attrs={
            "th": {"class": "title"},
        },
    )
    stores = TemplateColumn(
        verbose_name="Магазины",
        template_name="oscar/dashboard/catalogue/additional_row_stores.html",
        order_by="stores",
    )
    max_amount = Column(
        verbose_name="Максимум",
        order_by="max_amount",
    )
    weight = TemplateColumn(
        verbose_name="Вес",
        template_name="oscar/dashboard/catalogue/additional_row_weight.html",
        order_by="weight",
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
        attrs={
            "th": {"class": "actions"},
        },
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("is_public"),
    )

    icon = "fas fa-chart-bar"
    caption = ngettext_lazy("%s Дополнительный товар", "%s Дополнительных товара")

    class Meta(DashboardTable.Meta):
        model = Additional
        fields = (
            "check",
            "image",
            "name",
            "stores",
            "price",
            "old_price",
            "weight",
            "max_amount",
            "is_public",
        )
        sequence = (
            "check",
            "image",
            "name",
            "stores",
            "price",
            "old_price",
            "weight",
            "max_amount",
            "is_public",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых дополнительных товаров."



class CRMGroupEvotorTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/crm/groups/evotor_table/group_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/groups/evotor_table/group_row_name.html",
        order_by="name",
    )
    parent = TemplateColumn(
        verbose_name="Родительская группа",
        template_name="oscar/dashboard/crm/groups/evotor_table/group_row_parent.html",
        order_by="parent",
    )
    stores = TemplateColumn(
        verbose_name="Магазин",
        template_name="oscar/dashboard/crm/groups/evotor_table/group_row_store.html",
        order_by="store",
    )
    attributes = TemplateColumn(
        verbose_name="Атрибуты",
        template_name="oscar/dashboard/crm/groups/evotor_table/group_row_attributes.html",
        order_by="price",
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/crm/groups/evotor_table/group_row_date.html",
        order_by="updated_at",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/groups/evotor_table/group_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-object-group"
    caption = ngettext_lazy("%s Группа", "%s Групп")

    class Meta(DashboardTable.Meta):
        model = Category
        fields = (
            "check",
            "name",
            "parent",
            "stores",
            "attributes",
            "date_updated",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Список категорий и модификаций товаров."


class CRMGroupSiteTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/groups/site_table/category_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    image = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/category_row_image.html",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/groups/site_table/category_row_name.html",
        order_by="name",
    )
    description = TemplateColumn(
        template_code='{{ record.description|default:"-"|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}',
    )
    # mark_safe is needed because of
    # https://github.com/bradleyayers/django-tables2/issues/187
    num_children = LinkColumn(
        "dashboard:catalogue-category-detail-list",
        args=[A("pk")],
        verbose_name=mark_safe("Дочерние категории"),
        accessor=A("numchild"),
        orderable=True,
    )
    num_products = TemplateColumn(
        verbose_name="Товары",
        template_name="oscar/dashboard/catalogue/category_row_products.html",
        accessor=A("num_products"),
        orderable=True,
    )
    is_public = TemplateColumn(
        verbose_name="Доступен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by=("is_public"),
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/catalogue/category_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-layer-group"
    caption = ngettext_lazy("%s Категория", "%s Категорий")

    class Meta(DashboardTable.Meta):
        model = Category
        fields = ("image", "name", "description", "is_public")
        sequence = (
            "check",
            "image",
            "name",
            "description",
            "num_children",
            "num_products",
            "is_public",
            "...",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых категорий и модификаций товаров."
