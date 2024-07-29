
from django_tables2 import A, LinkColumn, TemplateColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class

DashboardTable = get_class("dashboard.tables", "DashboardTable")

class PaymentListTable(DashboardTable):

    id = LinkColumn("dashboard:payment-detail", args=[A("id")], verbose_name='Номер транзакции')

    amount = TemplateColumn(
        verbose_name="Сумма",
        template_name="oscar/dashboard/payments/payments_row_amount.html",
        accessor=A("amount"),
        order_by="amount.value",
    )

    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/payments/payments_row_status.html",
        accessor=A("status"),
        order_by="status",
    )
    
    paid = TemplateColumn(
        verbose_name="Оплачено",
        template_name="oscar/dashboard/payments/payments_row_paid.html",
        accessor=A("paid"),
        order_by="paid",
    )

    refundable = TemplateColumn(
        verbose_name="Возврат возможен",
        template_name="oscar/dashboard/payments/payments_row_refundable.html",
        accessor=A("refundable"),
        order_by="refundable",
    )

    order = TemplateColumn(
        verbose_name="Заказ",
        template_name="oscar/dashboard/payments/payments_row_order.html",
        accessor=A("description"),
        order_by="description",
    )

    created_at = TemplateColumn(
        verbose_name="Время создания",
        template_name="oscar/dashboard/payments/payments_row_created_at.html",
        accessor=A("created_at"),
        order_by="created_at",
    )

    actions = TemplateColumn(
        verbose_name="Действия",
        template_name="oscar/dashboard/payments/payments_row_actions.html",
        orderable=False,
    )

    icon = "sitemap"
    caption = ngettext_lazy("%s Платеж", "%s Платежей")

    class Meta(DashboardTable.Meta):
        fields = ("id", "order", "amount", "status", "paid", "refundable", "created_at", "actions")
        sequence = ("id", "order", "amount", "status", "paid", "refundable", "created_at", "..." , "actions")


class RefundListTable(DashboardTable):

    id = LinkColumn("dashboard:refund-detail", args=[A("id")], verbose_name='Номер транзакции')

    amount = TemplateColumn(
        verbose_name="Сумма",
        template_name="oscar/dashboard/payments/payments_row_amount.html",
        accessor=A("amount"),
        order_by="amount.value",
    )

    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/payments/payments_row_status.html",
        accessor=A("status"),
        order_by="status",
    )

    order = TemplateColumn(
        verbose_name="Заказ",
        template_name="oscar/dashboard/payments/payments_row_order.html",
        accessor=A("description"),
        order_by="description",
    )
    
    cancellation_details = TemplateColumn(
        verbose_name="Детали возврата",
        template_name="oscar/dashboard/payments/payments_row_cancellation_details.html",
        accessor=A("cancellation_details"),
        order_by="cancellation_details",
    )

    created_at = TemplateColumn(
        verbose_name="Время создания",
        template_name="oscar/dashboard/payments/payments_row_created_at.html",
        accessor=A("created_at"),
        order_by="created_at",
    )

    actions = TemplateColumn(
        verbose_name="Действия",
        template_name="oscar/dashboard/payments/refunds_row_actions.html",
        orderable=False,
    )

    icon = "sitemap"
    caption = ngettext_lazy("%s Возврат", "%s Возвратов")

    class Meta(DashboardTable.Meta):
        fields = ("id", "order", "amount", "status", "cancellation_details", "created_at", "actions")
        sequence = ("id", "order", "amount", "status", "cancellation_details", "created_at", "..." , "actions")
