from core.compat import get_user_model
from core.loading import get_class
from django_tables2 import A, Column, LinkColumn, TemplateColumn

DashboardTable = get_class("dashboard.tables", "DashboardTable")

User = get_user_model()


class UserTable(DashboardTable):
    check = TemplateColumn(
        template_name="dashboard/users/user_row_checkbox.html",
        verbose_name=" ",
        orderable=False,
    )
    phone = LinkColumn(
        "dashboard:user-detail",
        args=[A("id")],
        accessor="username",
        verbose_name="Номер телефона",
        attrs={
            "td": {"class": "name"},
        },
    )
    email = Column(
        accessor="email",
        order_by=("email"),
        verbose_name="Email",
    )
    first_name = Column(
        accessor="get_full_name",
        order_by=("first_name"),
        verbose_name="Имя клиента",
    )
    is_active = TemplateColumn(
        verbose_name="Активен",
        template_name="dashboard/table/boolean.html",
        order_by=("is_active"),
    )
    is_staff = TemplateColumn(
        verbose_name="Сотрудник",
        template_name="dashboard/table/boolean.html",
        order_by=("is_staff"),
    )
    telegram_id = TemplateColumn(
        verbose_name="Телеграм",
        template_name="dashboard/table/boolean.html",
        order_by=("telegram_id"),
    )
    num_orders = Column(
        accessor="userrecord__num_orders", default=0, verbose_name="Количество заказов"
    )
    date_registered = Column(accessor="date_joined")

    icon = "fas fa-users"

    class Meta(DashboardTable.Meta):
        model = User
        fields = (
            "phone",
            "email",
            "first_name",
            "is_active",
            "is_staff",
            "telegram_id",
            "date_registered",
        )
        sequence = (
            "check",
            "phone",
            "email",
            "first_name",
            "is_active",
            "is_staff",
            "telegram_id",
            "num_orders",
            "date_registered",
        )
        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Список пользователей пуст"
