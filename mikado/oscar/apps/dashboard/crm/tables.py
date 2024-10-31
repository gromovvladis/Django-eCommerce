from django.conf import settings
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django_tables2 import A, Column, LinkColumn, TemplateColumn, ManyToManyColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Partner = get_model("partner", "Partner")


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
        order_by="addresses",
        attrs = {'th': {'class': 'address'},}
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
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/crm/terminals/evotor_table/terminal_row_address.html",
        order_by="addresses",
        attrs = {'th': {'class': 'address'},}
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
    work_time = TemplateColumn(
        verbose_name="Время работы",
        template_name="oscar/dashboard/terminals/terminal_row_time.html",
        order_by="start_worktime",
        attrs = {'th': {'class': 'date'},}
    )
    staff = TemplateColumn(
        verbose_name="Персонал",
        template_name="oscar/dashboard/terminals/terminal_row_staff.html",
        order_by="users",
        attrs = {'th': {'class': 'staff'},}
    )
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/terminals/terminal_row_address.html",
        order_by="addresses",
        attrs = {'th': {'class': 'address'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/terminals/terminal_row_actions.html",
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
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/crm/staffs/evotor_table/staff_row_address.html",
        order_by="addresses",
        attrs = {'th': {'class': 'address'},}
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
            "address",
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
        verbose_name="Название",
        template_name="oscar/dashboard/crm/staffs/site_table/staff_row_name.html",
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
        template_name="oscar/dashboard/staff/staff_row_staff.html",
        order_by="users",
        attrs = {'th': {'class': 'staff'},}
    )
    address = TemplateColumn(
        verbose_name="Адрес",
        template_name="oscar/dashboard/staff/staff_row_address.html",
        order_by="addresses",
        attrs = {'th': {'class': 'address'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/staffs/staff_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Сотрудник", "%s Сотрудников")

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
        empty_text = "Нет созданых сотрудников"
