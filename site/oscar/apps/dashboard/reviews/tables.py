from django.urls import reverse_lazy
from django_tables2 import Column, TemplateColumn
from django.utils.translation import ngettext_lazy

from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
OrderReview = get_model("customer", "OrderReview")
ProductReview = get_model("reviews", "ProductReview")

class ReviewOrderTable(DashboardTable):
    checkbox = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/reviews/review_row_checkbox.html",
        orderable=False,
        attrs = {'th': {'class': 'checkbox'},}
    )
    name = TemplateColumn(
        verbose_name="Заказ",
        template_name="oscar/dashboard/reviews/review_row_order.html",
        order_by="order",
    )
    user = Column(
        verbose_name="Пользователь",
        orderable=True,
    )
    score = TemplateColumn(
        verbose_name="Оценка",
        template_name="oscar/dashboard/reviews/review_row_score.html",
        orderable=True,
    )
    body = TemplateColumn(
        verbose_name="Отзыв",
        template_name="oscar/dashboard/reviews/review_row_body.html",
        orderable=True,
    )
    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/reviews/review_row_status.html",
        order_by="status",
    )
    date_created = TemplateColumn(
        verbose_name="Дата создания",
        template_name="oscar/dashboard/reviews/review_row_date.html",
        orderable=True,
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/reviews/review_row_order_action.html",
        orderable=False,
    )
    
    icon = "fas fa-thumbs-up"
    caption = ngettext_lazy("%s Отзыв на заказ", "%s Отзыва на заказы")

    filter = {
        "url": reverse_lazy("dashboard:reviews-order-list"),
        "values": [
            ("", "Все"), 
            ("status=0", "Неизвестно"), 
            ("status=1", "Полезные"), 
            ("status=2", "Неполезные"),
        ]
    }

    class Meta(DashboardTable.Meta):
        model = OrderReview
        fields = (
            "name",
            "status",
            "user",
            "score",
            "body",
            "date_created",
        )
        sequence = (
            "checkbox",
            "name",
            "status",
            "user",
            "score",
            "body",
            "date_created",
            "actions",
            "..."
        )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        row_attrs = {
            'class': lambda record: 'new-record' if not record.is_open else ''
        }
        order_by = "date_created"
        empty_text = "Нет созданых отзывов на заказы"


class ReviewProductTable(DashboardTable):
    checkbox = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/reviews/review_row_checkbox.html",
        orderable=False,
        attrs = {'th': {'class': 'checkbox'},}
    )
    name = TemplateColumn(
        verbose_name="Товар",
        template_name="oscar/dashboard/reviews/review_row_product.html",
        order_by="product",
    )
    user = Column(
        verbose_name="Пользователь",
        orderable=True,
    )
    score = TemplateColumn(
        verbose_name="Оценка",
        template_name="oscar/dashboard/reviews/review_row_score.html",
        orderable=True,
    )
    body = TemplateColumn(
        verbose_name="Отзыв",
        template_name="oscar/dashboard/reviews/review_row_body.html",
        orderable=True,
    )
    status = TemplateColumn(
        verbose_name="Статус",
        template_name="oscar/dashboard/reviews/review_row_status.html",
        order_by="status",
    )
    date_created = TemplateColumn(
        verbose_name="Дата создания",
        template_name="oscar/dashboard/reviews/review_row_date.html",
        orderable=True,
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/reviews/review_row_product_action.html",
        orderable=False,
    )
    
    icon = "fas fa-thumbs-up"
    caption = ngettext_lazy("%s Отзыв на товар", "%s Отзывов на товары")

    filter = {
        "url": reverse_lazy("dashboard:reviews-product-list"),
        "values": [
            ("", "Все"), 
            ("status=0", "Неизвестно"), 
            ("status=1", "Полезные"), 
            ("status=2", "Неполезные"),
        ]
    }

    class Meta(DashboardTable.Meta):
        model = ProductReview
        fields = (
            "name",
            "status",
            "user",
            "score",
            "body",
            "date_created",
        )
        sequence = (
            "checkbox",
            "name",
            "status",
            "user",
            "score",
            "body",
            "date_created",
            "actions",
            "..."
        )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
        }
        row_attrs = {
            'class': lambda record: 'new-record' if not record.is_open else ''
        }
        order_by = "date_created"
        empty_text = "Нет созданых отзывов на товары"

