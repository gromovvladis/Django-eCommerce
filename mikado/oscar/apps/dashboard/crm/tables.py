from django_tables2 import A, Column, LinkColumn, TemplateColumn, ManyToManyColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Partner = get_model("partner", "Partner")
Terminal = get_model("partner", "Terminal")
Staff = get_model("user", "Staff")


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
    evotor_id = Column(
        verbose_name="Эвотор ID",
        order_by="evotor_id",
        attrs = {'th': {'class': 'evotor_id'},}
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
        order_by="date_updated",
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
            "evotor_id",
        )
        sequence = (
            "check",
            "name",
            "evotor_id",
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
    evotor_id = Column(
        verbose_name="Эвотор ID",
        order_by="evotor_id",
        attrs = {'th': {'class': 'evotor_id'},}
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
        verbose_name="Дата",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_date.html",
        order_by="date_updated",
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
            "evotor_id",
            "model",
            "imei",
            "date",
        )
        sequence = (
            "check",
            "name",
            "evotor_id",
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
    evotor_id = Column(
        verbose_name="Эвотор ID",
        order_by="evotor_id",
        attrs = {'th': {'class': 'evotor_id'},}
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
        order_by="date_updated",
        attrs = {'th': {'class': 'date'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Сотрудник Эвотор", "%s Сотрудники Эвотор")

    class Meta(DashboardTable.Meta):
        model = Partner
        fields = (
            "name",
            "evotor_id",
        )
        sequence = (
            "check",
            "name",
            "evotor_id",
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
