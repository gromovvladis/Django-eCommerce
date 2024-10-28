
from django_tables2 import A, TemplateColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class

DashboardTable = get_class("dashboard.tables", "DashboardTable")

class PaymentListTable(DashboardTable):

    order = TemplateColumn(
        verbose_name="Заказ",
        template_name="oscar/dashboard/payments/transaction_row_order.html",
        accessor=A("description"),
        order_by="description",
        attrs = {'th': {'class': 'name'},
                 'td': {'class': 'name'},
        },
    )

    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/payments/transaction_row_status.html",
        accessor=A("status"),
        order_by="status",
        attrs = {'th': {'class': 'status'},}
    )

    amount = TemplateColumn(
        verbose_name="Сумма",
        template_name="oscar/dashboard/payments/transaction_row_amount.html",
        accessor=A("amount"),
        order_by="amount.value",
        attrs = {'th': {'class': 'price'}}
    )

    paid = TemplateColumn(
        verbose_name="Оплачено",
        template_name="oscar/dashboard/table/boolean.html",
        accessor=A("paid"),
        order_by="paid",
        attrs = {'th': {'class': 'paid'},}
    )

    refundable = TemplateColumn(
        verbose_name="Возврат возможен",
        template_name="oscar/dashboard/table/boolean.html",
        accessor=A("refundable"),
        order_by="refundable",
        attrs = {'th': {'class': 'paid'},}
    )

    created_at = TemplateColumn(
        verbose_name="Время создания",
        template_name="oscar/dashboard/payments/transaction_row_created_at.html",
        accessor=A("created_at"),
        order_by="created_at",
        attrs = {'th': {'class': 'date'},}
    )

    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/payments/payment_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "sitemap"
    caption = ngettext_lazy("%s Платеж", "%s Платежей")

    class Meta(DashboardTable.Meta):
        fields = ("order", "amount", "status", "paid", "refundable", "created_at", "actions")
        sequence = ("order", "amount", "status", "paid", "refundable", "created_at", "..." , "actions")

        empty_text = "Нет созданых платежей"

class RefundListTable(DashboardTable):

    order = TemplateColumn(
        verbose_name="Заказ",
        template_name="oscar/dashboard/payments/transaction_row_order.html",
        accessor=A("description"),
        order_by="description",
        attrs = {'th': {'class': 'name'},
                 'td': {'class': 'name'},
        },
    )

    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/payments/transaction_row_status.html",
        accessor=A("status"),
        order_by="status",
        attrs = {'th': {'class': 'status'},}
    )
    
    amount = TemplateColumn(
        verbose_name="Сумма",
        template_name="oscar/dashboard/payments/transaction_row_amount.html",
        accessor=A("amount"),
        order_by="amount.value",
        attrs = {'th': {'class': 'price'}}
    )

    cancellation_details = TemplateColumn(
        verbose_name="Детали возврата",
        template_name="oscar/dashboard/payments/refund_row_cancellation_details.html",
        accessor=A("cancellation_details"),
        order_by="cancellation_details",
    )

    created_at = TemplateColumn(
        verbose_name="Время создания",
        template_name="oscar/dashboard/payments/transaction_row_created_at.html",
        accessor=A("created_at"),
        order_by="created_at",
    )

    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/payments/refund_row_actions.html",
        orderable=False,
        attrs = {'th': {'class': 'actions'},}
    )

    icon = "sitemap"
    caption = ngettext_lazy("%s Возврат", "%s Возвратов")

    class Meta(DashboardTable.Meta):
        fields = ("order", "amount", "status", "cancellation_details", "created_at", "actions")
        sequence = ("order", "amount", "status", "cancellation_details", "created_at", "..." , "actions")

        empty_text = "Нет созданых возвратов"
