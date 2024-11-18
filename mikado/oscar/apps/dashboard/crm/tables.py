from django_tables2 import A, Column, LinkColumn, TemplateColumn, ManyToManyColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Partner = get_model("partner", "Partner")
Terminal = get_model("partner", "Terminal")
Staff = get_model("user", "Staff")
Product = get_model('catalogue', 'Product')


class CRMPartnerEvotorTable(DashboardTable):
    
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/partners/evotor_table/partner_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/partners/evotor_table/partner_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    id = Column(
        verbose_name="Эвотор ID",
        order_by="id",
        attrs = {'th': {'class': 'id'},}
    )
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/crm/partners/evotor_table/partner_row_address.html",
        order_by="address",
        attrs = {'th': {'class': 'address'},}
    )
    date = TemplateColumn(
        verbose_name="Дата",
        template_name="oscar/dashboard/crm/partners/evotor_table/partner_row_date.html",
        order_by="updated_at",
        attrs = {'th': {'class': 'date'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/partners/evotor_table/partner_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Магазин Эвотор", "%s Магазинов Эвотор")

    class Meta(DashboardTable.Meta):
        model = Partner
        fields = (
            "name",
            "id",
        )
        sequence = (
            "check",
            "name",
            "id",
            "address",
            "date",
            "actions",
        )
        
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых точек продажи Эвотор"


class CRMPartnerSiteTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/crm/partners/site_table/partner_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/partners/site_table/partner_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    work_time = TemplateColumn(
        verbose_name="Время работы",
        template_name="oscar/dashboard/partners/partner_row_time.html",
        order_by="start_worktime",
        attrs = {'th': {'class': 'date'},}
    )
    staff = TemplateColumn(
        verbose_name="Персонал",
        template_name="oscar/dashboard/partners/partner_row_staff.html",
        order_by="users",
        attrs = {'th': {'class': 'staff'},}
    )
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/partners/partner_row_address.html",
        order_by="addresses",
        attrs = {'th': {'class': 'address'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/partners/partner_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Точка продажи", "%s Точки продаж")

    class Meta(DashboardTable.Meta):
        model = Partner
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
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых точек продажи"

# ===========================================

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
        attrs = {'th': {'class': 'name'},}
    )
    id = Column(
        verbose_name="Эвотор ID",
        order_by="id",
        attrs = {'th': {'class': 'id'},}
    )
    partners = TemplateColumn(
        verbose_name="Магазин",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_partner.html",
        order_by="store_id",
        attrs = {'th': {'class': 'partners'},}
    )
    model = Column(
        verbose_name="Модель",
        order_by="model",
        attrs = {'th': {'class': 'model'},}
    )
    imei = Column(
        verbose_name="IMEI",
        order_by="imei",
        attrs = {'th': {'class': 'imei'},}
    )
    date = TemplateColumn(
        verbose_name="Обновлен",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_date.html",
        order_by="updated_at",
        attrs = {'th': {'class': 'date'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
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
            "date",
        )
        sequence = (
            "check",
            "name",
            "id",
            "partners",
            "model",
            "imei",
            "date",
            "actions",
        )
        
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых терминалов Эвотор"


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
        attrs = {'th': {'class': 'name'},}
    )
    partners = TemplateColumn(
        verbose_name="Точки продаж",
        template_name="oscar/dashboard/partners/terminal_row_partner.html",
        order_by="partner",
        attrs = {'th': {'class': 'partners'},}
    )
    model = Column(
        verbose_name="Модель",
        order_by="model",
        attrs = {'th': {'class': 'model'},}
    )
    imei = Column(
        verbose_name="IMEI",
        order_by="imei",
        attrs = {'th': {'class': 'imei'},}
    )
    date_created = TemplateColumn(
        verbose_name="Создан",
        template_name="oscar/dashboard/partners/terminal_row_date_created.html",
        order_by="date_created",
        attrs = {'th': {'class': 'date_created'},}
    )
    date_updated = TemplateColumn(
        verbose_name="Изменен",
        template_name="oscar/dashboard/partners/terminal_row_date_updated.html",
        order_by="date_updated",
        attrs = {'th': {'class': 'date_created'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/partners/terminal_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-tablet-screen-button"
    caption = ngettext_lazy("%s Терминал", "%s Терминалов")

    class Meta(DashboardTable.Meta):
        model = Terminal
        fields = (
            "name",
            "partners",
            "model",
            "imei",
            "date_created",
            "date_updated",
        )
        sequence = (
            "check",
            "name",
            "partners",
            "model",
            "imei",
            "date_created",
            "date_updated",
            "actions",
        )
        
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых терминалов"

# ===========================================

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
        attrs = {'th': {'class': 'name'},}
    )
    id = Column(
        verbose_name="Эвотор ID",
        order_by="id",
        attrs = {'th': {'class': 'id'},}
    )
    role = Column(
        verbose_name="Должность",
        order_by="role",
        attrs = {'th': {'class': 'role'},}
    )
    phone = Column(
        verbose_name="Пользователь",
        order_by="phone",
        attrs = {'th': {'class': 'phone'},}
    )
    partners = TemplateColumn(
        verbose_name="Точки продаж",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_partners.html",
        order_by="partners",
        attrs = {'th': {'class': 'partners'},}
    )
    date = TemplateColumn(
        verbose_name="Дата",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_date.html",
        order_by="updated_at",
        attrs = {'th': {'class': 'date'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-user-group"
    caption = ngettext_lazy("%s Сотрудник Эвотор", "%s Сотрудники Эвотор")

    class Meta(DashboardTable.Meta):
        model = Partner
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
            "partners",
            "date",
            "actions",
        )
        
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых сотрудников Эвотор"


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
        attrs = {'th': {'class': 'name'},}
    )
    role = TemplateColumn(
        verbose_name="Должность",
        template_name="oscar/dashboard/partners/staff_row_role.html",
        order_by="role",
        attrs = {'th': {'class': 'role'},}
    )
    user = TemplateColumn(
        verbose_name="Пользователь",
        template_name="oscar/dashboard/partners/staff_row_user.html",
        order_by="user",
        attrs = {'th': {'class': 'user'},}
    )
    partners = TemplateColumn(
        verbose_name="Точки продаж",
        template_name="oscar/dashboard/partners/staff_row_partners.html",
        order_by="partners",
        attrs = {'th': {'class': 'partners'},}
    )
    notif = TemplateColumn(
        verbose_name="Уведопления",
        template_name="oscar/dashboard/partners/staff_row_notif.html",
        order_by="telegram",
        attrs = {'th': {'class': 'notif'},}
    )
    age = Column(
        verbose_name="Возраст",
        order_by="age",
        attrs = {'th': {'class': 'age'},}
    )
    is_active = TemplateColumn(
        verbose_name="Активен",
        template_name="oscar/dashboard/table/boolean.html",
        order_by="is_active",
        attrs = {'th': {'class': 'active'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/partners/staff_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
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
            "partners",
            "notif",
            "age",
            "is_active",
            "actions",
        )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Список сотрудников пуст"

# ===========================================

class CRMProductEvotorTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    description = Column(
        verbose_name="Описание",
        order_by="description",
        attrs = {'th': {'class': 'description'},}
    )
    parent = TemplateColumn(
        verbose_name="Родительский товар",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_parent.html",
        order_by="parent",
        attrs = {'th': {'class': 'parent'},}
    )
    partners = TemplateColumn(
        verbose_name="Точка продажи",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_partner.html",
        order_by="partner",
        attrs = {'th': {'class': 'partners'},}
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_price.html",
        order_by="price",
        attrs = {'th': {'class': 'price'},}
    )
    tax = Column(
        verbose_name="Налог",
        order_by="tax",
        attrs = {'th': {'class': 'age'},}
    )
    measure_name = Column(
        verbose_name="Ед. измерения",
        order_by="measure_name",
        attrs = {'th': {'class': 'measure_name'},}
    )
    allow_to_sell = TemplateColumn(
        verbose_name="Доступен",        
        template_name="oscar/dashboard/table/boolean.html",
        order_by="allow_to_sell",
        attrs = {'th': {'class': 'allow_to_sell'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-cookie-bite"
    caption = ngettext_lazy("%s Продукт", "%s Продуктов")

    class Meta(DashboardTable.Meta):
        model = Staff
        fields = (
            "check",
            "name",
            "description",
            "parent",
            "partners",
            "price",
            "tax",
            "measure_name",
            "allow_to_sell",
            "actions",
        )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Список продуктов пуст"


class CRMProductSiteTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/products/site_table/product_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    image = TemplateColumn(
        verbose_name='',
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
        attrs = {'th': {'class': 'image'},}
    )
    title = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/products/site_table/product_row_title.html",
        order_by="title",
        accessor=A("title"),
        attrs = {'th': {'class': 'title'},}
    )
    variants = TemplateColumn(
        verbose_name="Варианты",
        template_name="oscar/dashboard/catalogue/product_row_variants.html",
        orderable=True,
        attrs = {'th': {'class': 'variants'},}
    )
    additionals = TemplateColumn(
        verbose_name="Доп. товары",
        template_name="oscar/dashboard/catalogue/product_row_additionals.html",
        orderable=True,
        order_by="productadditional",
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
        order_by="min_price",
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

    date_updated = TemplateColumn(
        template_code='{{ record.date_updated|date:"d.m.y H:i" }}',
        attrs = {'th': {'class': 'date_updated'}}
    )

    icon = "fas fa-chart-bar"
    caption = ngettext_lazy("%s Продукт", "%s Продуктов")

    class Meta(DashboardTable.Meta):
        model = Product
        fields = ("date_updated", "is_public")
        sequence = (
            "check",
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

# ===========================================


class CRMGroupEvotorTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    description = Column(
        verbose_name="Описание",
        order_by="description",
        attrs = {'th': {'class': 'description'},}
    )
    parent = TemplateColumn(
        verbose_name="Родительский товар",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_parent.html",
        order_by="parent",
        attrs = {'th': {'class': 'parent'},}
    )
    partners = TemplateColumn(
        verbose_name="Точка продажи",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_partner.html",
        order_by="partner",
        attrs = {'th': {'class': 'partners'},}
    )
    price = TemplateColumn(
        verbose_name="Цена",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_price.html",
        order_by="price",
        attrs = {'th': {'class': 'price'},}
    )
    tax = Column(
        verbose_name="Налог",
        order_by="tax",
        attrs = {'th': {'class': 'age'},}
    )
    measure_name = Column(
        verbose_name="Ед. измерения",
        order_by="measure_name",
        attrs = {'th': {'class': 'measure_name'},}
    )
    allow_to_sell = TemplateColumn(
        verbose_name="Доступен",        
        template_name="oscar/dashboard/table/boolean.html",
        order_by="allow_to_sell",
        attrs = {'th': {'class': 'allow_to_sell'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/products/evotor_table/product_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-cookie-bite"
    caption = ngettext_lazy("%s Продукт", "%s Продуктов")

    class Meta(DashboardTable.Meta):
        model = Staff
        fields = (
            "check",
            "name",
            "description",
            "parent",
            "partners",
            "price",
            "tax",
            "measure_name",
            "allow_to_sell",
            "actions",
        )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Список продуктов пуст"


class CRMGroupSiteTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/products/site_table/product_row_checkbox.html",
        verbose_name="",
        orderable=False,
    )
    image = TemplateColumn(
        verbose_name='',
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
        attrs = {'th': {'class': 'image'},}
    )
    title = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/crm/products/site_table/product_row_title.html",
        order_by="title",
        accessor=A("title"),
        attrs = {'th': {'class': 'title'},}
    )
    variants = TemplateColumn(
        verbose_name="Варианты",
        template_name="oscar/dashboard/catalogue/product_row_variants.html",
        orderable=True,
        attrs = {'th': {'class': 'variants'},}
    )
    additionals = TemplateColumn(
        verbose_name="Доп. товары",
        template_name="oscar/dashboard/catalogue/product_row_additionals.html",
        orderable=True,
        order_by="productadditional",
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
        order_by="min_price",
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

    date_updated = TemplateColumn(
        template_code='{{ record.date_updated|date:"d.m.y H:i" }}',
        attrs = {'th': {'class': 'date_updated'}}
    )

    icon = "fas fa-chart-bar"
    caption = ngettext_lazy("%s Продукт", "%s Продуктов")

    class Meta(DashboardTable.Meta):
        model = Product
        fields = ("date_updated", "is_public")
        sequence = (
            "check",
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
