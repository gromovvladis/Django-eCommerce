from django_tables2 import A, Column, LinkColumn, TemplateColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

from django.contrib.auth.models import Group

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Partner = get_model("partner", "Partner")
Staff = get_model("user", "Staff")


class PartnerListTable(DashboardTable):

    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/partners/partner_row_name.html",
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
    caption = ngettext_lazy("%s Точка продажи", "%s Точек продаж")

    class Meta(DashboardTable.Meta):
        model = Partner
        fields = (
            "name",
        )
        sequence = (
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


class GroupListTable(DashboardTable):

    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/partners/group_row_name.html",
        order_by="name",
        attrs = {'th': {'class': 'name'},}
    )
    permission = TemplateColumn(
        verbose_name="Права пользователя",
        template_name="oscar/dashboard/partners/group_row_permission.html",
        order_by="start_worktime",
        attrs = {'th': {'class': 'permission'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/partners/group_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "fas fa-id-card-clip"
    caption = ngettext_lazy("%s Группа персонала", "%s Группы персонала")

    class Meta(DashboardTable.Meta):
        model = Group
        fields = (
            "name",
        )
        
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых групп продажи"


class StaffListTable(DashboardTable):

    check = TemplateColumn(
        template_name="oscar/dashboard/users/user_row_checkbox.html",
        verbose_name=" ",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/partners/staff_row_name.html",
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
            "notif",
            "age",
            "is_active",
            "actions",
        )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        empty_text = "Нет созданых групп продажи"
