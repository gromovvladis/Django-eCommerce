from django_tables2 import A, Column, LinkColumn, TemplateColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")

FlatPage = get_model("flatpages", "FlatPage")


class PagesTable(DashboardTable):
    title = LinkColumn(
        "dashboard:page-update",
        args=[A("id")],
        verbose_name="Название",
        order_by="title",
    )
    url = TemplateColumn(
        verbose_name="URL",
        template_name="oscar/dashboard/pages/page_row_url.html",
        order_by="url",
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/pages/page_row_actions.html",
        orderable=False,
        attrs={
            "th": {"class": "actions"},
        },
    )

    icon = "fas fa-house"
    caption = ngettext_lazy("%s Страница", "%s Страниц")

    class Meta(DashboardTable.Meta):
        model = FlatPage
        fields = (
            "title",
            "url",
        )
        sequence = (
            "title",
            "url",
            "actions",
        )

        attrs = {
            "class": "table table-striped table-bordered table-hover",
        }
        empty_text = "Нет созданых страниц."
