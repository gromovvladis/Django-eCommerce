from django_tables2 import A, Column, LinkColumn, TemplateColumn
from django.contrib.auth.models import Group

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")

Store = get_model("store", "Store")
StoreCashTransaction = get_model("store", "StoreCashTransaction")
Terminal = get_model("store", "Terminal")
Staff = get_model("user", "Staff")


class StoreListTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/stores/store_row_name.html",
        order_by="name",
    )
    work_time = TemplateColumn(
        verbose_name="Время работы",
        template_name="oscar/dashboard/stores/store_row_time.html",
        order_by="start_worktime",
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
        template_name="oscar/dashboard/stores/store_row_actions.html",
        orderable=False,attrs={
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
            "is_active",
        )
        sequence = (
            "name",
            "work_time",
            "staff",
            "address",
            "is_active",
            "actions",
        )

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых точек продажи."


class StoreCashTransactionListTable(DashboardTable):
    type = TemplateColumn(
        verbose_name="Транзакция",
        template_name="oscar/dashboard/stores/store_cash_transaction_row_type.html",
        order_by="type",
        attrs={
            "th": {"class": "status"},
            "td": {"class": "status"},
        },
    )
    sum = TemplateColumn(
        verbose_name="Наличные",
        template_name="oscar/dashboard/stores/store_cash_transaction_row_sum.html",
        order_by="sum",
        attrs={
            "th": {"class": "name"},
            "td": {"class": "name"},
        },
    )
    order = LinkColumn(
        "dashboard:order-detail",
        args=[A("order.number")],
        order_by="order__number",
        verbose_name="Номер заказа",
    )
    description = Column(
        verbose_name="Описание",
        order_by="description",
    )
    user = TemplateColumn(
        verbose_name="Пользователь",
        template_name="oscar/dashboard/stores/store_cash_transaction_user.html",
        order_by="user",
    )
    date_created = TemplateColumn(
        verbose_name="Дата",
        template_code='{{ record.date_created|date:"d.m.y H:i" }}',
        order_by="date_created",
    )

    icon = "fas fa-id-card-clip"
    caption = ngettext_lazy(
        "%s Внесение / Изъятие наличиных", "%s Внесений / Изъятий наличиных"
    )

    class Meta(DashboardTable.Meta):
        model = StoreCashTransaction
        fields = (
            "type",
            "sum",
            "description",
            "order",
            "user",
            "date_created",
        )
        order_by = "-date_created"
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Список внесений и транзакций пуст."


class StaffListTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/users/user_row_checkbox.html",
        verbose_name=" ",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/stores/staff_row_name.html",
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
    age = TemplateColumn(
        verbose_name="Возраст",
        template_name="oscar/dashboard/stores/staff_row_age.html",
        order_by="date_of_birth",
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
            "name",
            "role",
            "user",
            "stores",
            "notif",
            "age",
            "is_active",
        )
        sequence = (
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


class StoreStaffListTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Имя",
        template_name="oscar/dashboard/stores/staff_row_name.html",
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
        template_name="oscar/dashboard/stores/store_staff_row_actions.html",
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
            "name",
            "role",
            "user",
            "stores",
            "is_active",
            "actions",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Список персонала пуст."


class TerminalListTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/stores/terminal_row_name.html",
        order_by="name",
    )
    store = TemplateColumn(
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
        attrs={
            "th": {"class": "date_created"},
        },
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
            "model",
            "imei",
            "date_created",
            "date_updated",
        )
        sequence = (
            "name",
            "store",
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


class GroupListTable(DashboardTable):
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/stores/group_row_name.html",
        order_by="name",
    )
    permission = TemplateColumn(
        verbose_name="Права пользователя",
        template_name="oscar/dashboard/stores/group_row_permission.html",
        order_by="start_worktime",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/stores/group_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-id-card-clip"
    caption = ngettext_lazy("%s Группа персонала", "%s Группы персонала")

    class Meta(DashboardTable.Meta):
        model = Group
        fields = ("name",)

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых групп персонала."
