from django.conf import settings
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django_tables2 import A, Column, LinkColumn, TemplateColumn, ManyToManyColumn

from django.utils.translation import ngettext_lazy
from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Partner = get_model("partner", "Partner")


class CRMPartnerListTable(DashboardTable):
    
    check = TemplateColumn(
        template_name="oscar/dashboard/crm/partners/partner_row_checkbox.html",
        verbose_name=" ",
        orderable=False,
    )
    name = TemplateColumn(
        verbose_name="Название",
        template_name="oscar/dashboard/crm/partners/partner_row_name.html",
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
        template_name="oscar/dashboard/crm/partners/partner_row_address.html",
        order_by="addresses",
        attrs = {'th': {'class': 'address'},}
    )
    actions = TemplateColumn(
        verbose_name="",
        template_name="oscar/dashboard/crm/partners/partner_row_actions.html",
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
        empty_text = "Нет созданых точек продажи"

