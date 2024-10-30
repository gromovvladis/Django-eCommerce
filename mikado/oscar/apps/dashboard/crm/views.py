from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, fields
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, UpdateView, DeleteView, CreateView, View
from django_tables2 import MultiTableMixin, RequestConfig, SingleTableView
from django.views.generic.edit import FormMixin
from django.utils import timezone

from django.views.generic import TemplateView
from oscar.apps.partner.models import PartnerAddress
from oscar.views.generic import BulkEditMixin
from oscar.apps.crm.client import EvatorCloud
from oscar.apps.partner.serializers import PartnersSerializer
from oscar.core.loading import get_class, get_classes, get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.encoding import smart_str
from django.views.generic.base import View

from oscar.core.utils import safe_referrer

import logging
logger = logging.getLogger("oscar.dashboard")

Partner = get_model("partner", "Partner")
Order = get_model("order", "Order")
Line = get_model("order", "Line")


(
    CRMPartnerListTable,
    # CRMPartnerTable,
) = get_classes(
    "dashboard.crm.tables",
    (
        "CRMPartnerListTable",
        # "ProductClassSelectForm",
    ),
)

(
    PartnerListTable,
    # CRMPartnerTable,
) = get_classes(
    "dashboard.partners.tables",
    (
        "PartnerListTable",
        # "ProductClassSelectForm",
    ),
)

class CRMOrderListView(View):
    # template_name = 'oscar/dashboard/crm/crm_orders_list.html'
    # table_class = CRMOrderTable
    # context_table_name = "orders"
    # paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    
    template_name = 'oscar/dashboard/crm/test_list.html'
    context_object_name = "test"
    
    # def get_queryset(self):
    def get_context_data(self):
        try:
            res = EvatorCloud().get_terminals()
        except Exception as e:
            res = []
            logger.error("Error CRMOrderListView - %s" % str(e))

        return res
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(request, self.template_name, {self.context_object_name: context})


class CRMPartnerListView(MultiTableMixin, TemplateView):
    template_name = 'oscar/dashboard/crm/partners/partner_list.html'
    model = Partner
    context_table_name = "tables"
    paginate_by = settings.OSCAR_EVOTOR_ITEMS_PER_PAGE
 
    table_prefix = "partner_{}-"


    def dispatch(self, request, *args, **kwargs):
        self.queryset = self.get_queryset()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        update_all = request.POST.get("update_all", 'False')
        if update_all == 'True':
            partners = self.get_queryset()
            return self.update_partners(request, partners)
        
        ids = request.POST.getlist("selected_%s" % self.get_checkbox_object_name())
        ids = list(map(str, ids))
        if not ids:
            messages.error(
                self.request,
                ("Вам нужно выбрать несколько точек продажи"),
            )
            return redirect("dashboard:crm-partners")

        partners = self.get_objects(ids)
        return self.update_partners(request, partners)
    
    def get_queryset(self):
        
        # partners_json = EvatorCloud().get_partners() 
        partners_json = {
            'items': [
                {
                    'id': '20240713-96AB-40D1-80FA-D455E402869E',
                    'name': 'Мой магазин',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T03:44:04.000+0000',
                    'updated_at': '2024-07-13T05:53:32.000+0000'
                },
                {
                    'id': '20240713-774A-4038-8037-E66BF3AA7552',
                    'address': '9 Мая 77',
                    'name': 'Прованс',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-774A-4038-8037-E66BF3AA7442',
                    'name': 'Микадо',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                                {
                    'id': '20240713-774A-4038-8037-E66BF3AA7444',
                    'name': 'Микадо2',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                                {
                    'id': '20240713-774A-4038-8037-E66Bh3AA7442',
                    'name': 'GREGRR',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-774A-4058-8037-E66BF3AA7442',
                    'name': 'Пивная',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-274A-4038-8037-E66BF3AA7442',
                    'name': 'столовая',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-274A-4038-8037-E66B36AA7442',
                    'name': 'Суши',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '23240713-274A-4038-8037-E66B36AA7442',
                    'name': 'Ярмарка',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-96AB-42D1-80FA-D455E402869E',
                    'name': 'Мой магазин 1',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T03:44:04.000+0000',
                    'updated_at': '2024-07-13T05:53:32.000+0000'
                },
                {
                    'id': '20240713-774A-3038-8867-E66BF3AA7552',
                    'address': '9 Мая 77',
                    'name': 'Прованс 3',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-776A-4038-8037-E66BF3AA7442',
                    'name': 'Микадо4',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                                {
                    'id': '202fr713-774A-4038-8037-E66BF3AA7444',
                    'name': 'Микадо 453',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                                {
                    'id': '2024f713-774A-4038-8037-E66Bh3AA7442',
                    'name': 'ЧТО-ТО',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240714-444A-4058-8037-E66BF3AA7442',
                    'name': 'Пивная 2',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-234а-4038-8037-E66BF3AA7442',
                    'name': 'столовая 2',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '21110713-274A-4038-8037-E66B36AA7442',
                    'name': 'Суши 342',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '23200013-274A-4038-8037-E66B36AA7442',
                    'name': 'Ярмарка 2',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240714-444A-4058-8037-E66BF3A00442',
                    'name': 'Пивная 24',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-234а-4038-8037-E66BF3AA7000',
                    'name': 'столовая вкусная',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '21110713-274A-4038-8037-E66B36444442',
                    'name': 'Суши очень',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '23200013-2444-4038-8037-E66B36AA7442',
                    'name': 'Ярмарка 543',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                }
            ],
            'paging': {}
        }
        serializer = PartnersSerializer(data=partners_json)

        if serializer.is_valid():
            deserialized_data = serializer.validated_data
            partners = deserialized_data['items']
            
            for partner_data in partners:
                evotor_id = partner_data['evotor_id']  # Идентификатор партнера
                name = partner_data['name']
                address = partner_data.get('address')  # Может отсутствовать
                
                # Проверяем, существует ли партнер с данным evotor_id в базе
                partner_instance = Partner.objects.filter(evotor_id=evotor_id).first()
                
                if partner_instance:
                    # Партнер существует: проверяем совпадение полей
                    partner_data['is_created'] = True
                    # Проверка совпадения полей
                    address_matches = (address == (partner_instance.primary_address.line1 if partner_instance.primary_address else None))
                    partner_data['is_valid'] = partner_instance.name == name and address_matches
                else:
                    # Партнер не существует
                    partner_data['is_created'] = False
                    partner_data['is_valid'] = False

            self.queryset = partners
            return partners
        else:
            return serializer.errors
    
    def get_objects(self, ids):
        partner_list = self.get_queryset()
        filtered_list = [partner for partner in partner_list if partner['evotor_id'] in ids]
        return filtered_list

    def update_partners(self, request, partners_data):
        partners = []
        for partner_data in partners_data:
            # Получаем данные партнера
            evotor_id = partner_data['evotor_id']
            name = partner_data['name']
            address = partner_data.get('address')  # Может отсутствовать

            # Ищем партнера по evotor_id
            partner, created = Partner.objects.update_or_create(
                evotor_id=evotor_id,
                defaults={
                    'name': name,
                    'date_updated': timezone.now()  # Обновляем поле изменения
                }
            )
            partners.append(partner)

            # Обновляем или создаем адрес, если он указан
            if address:
                partner_address, address_created = PartnerAddress.objects.update_or_create(
                    partner=partner,
                    defaults={'line1': address}
                )
            elif partner.primary_address:
                partner.addresses.first().delete()

        messages.success(
            self.request,
            ("Точки продажи были успешно обновлены"),
        )
        return redirect("dashboard:crm-partners")
    
    def get_checkbox_object_name(self):
        return smart_str(self.model._meta.object_name.lower())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        stauses = self.get_evotor_statuses()
        ctx['is_valid'] = stauses['is_valid']
        ctx['not_is_valid'] = stauses['not_is_valid'] 
        ctx['wrong_evotor_id'] = stauses['wrong_evotor_id']
        return ctx
    
    def get_evotor_statuses(self):
        stauses = {}
        evotor_pertners = self.queryset
        stauses['is_valid'] = is_valid = sum(1 for item in evotor_pertners if item.get('is_valid') is True)
        stauses['not_is_valid'] = len(evotor_pertners) - is_valid
        evotor_ids = [partner['evotor_id'] for partner in evotor_pertners]
        stauses['wrong_evotor_id'] = Partner.objects.filter(evotor_id__isnull=False).exclude(evotor_id__in=evotor_ids).count()
        return stauses
    
    def get_tables(self):
        return [
            self.get_evotor_partners_table(),
            self.get_site_partners_table(),
        ]
    
    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_evotor_partners_table(self):
        return CRMPartnerListTable(self.queryset)

    def get_site_partners_table(self):
        evotor_ids = [partner['evotor_id'] for partner in self.queryset]
        return PartnerListTable(
            Partner.objects.filter(evotor_id__isnull=False).exclude(evotor_id__in=evotor_ids)
        )


class CRMStaffListView(View):
    # template_name = 'oscar/dashboard/crm/crm_staffs_list.html'
    # table_class = CRMStaffTable
    # context_table_name = "staffs"
    # paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    
    template_name = 'oscar/dashboard/crm/test_list.html'
    context_object_name = "test"
    
    def get_context_data(self):
        try:
            res = EvatorCloud().get_staffs()
        except Exception as e:
            res = []
            logger.error("Error CRMStaffListView - %s" % str(e))

        return res
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(request, self.template_name, {self.context_object_name: context})


class CRMProductListView(View):
    # template_name = 'oscar/dashboard/crm/crm_products_list.html'
    # table_class = CRMProductTable
    # context_table_name = "products"
    # paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    
    template_name = 'oscar/dashboard/crm/test_list.html'
    context_object_name = "test"
    
    def get_context_data(self):
        try:
            res = EvatorCloud().get_products()
        except Exception as e:
            res = []
            logger.error("Error CRMProductListView - %s" % str(e))

        return res
    
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(request, self.template_name, {self.context_object_name: context})
    

class CRMReceiptListView(View):
    # template_name = 'oscar/dashboard/crm/crm_receipts_list.html'
    # table_class = CRMReceiptTable
    # context_table_name = "receipts"
    # paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    
    template_name = 'oscar/dashboard/crm/test_list.html'
    context_object_name = "test"
    
    def get_context_data(self):
        try:
            res = EvatorCloud().get_terminals()
        except Exception as e:
            res = []
            logger.error("Error CRMReceiptListView - %s" % str(e))

        return res

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(request, self.template_name, {self.context_object_name: context})
    

class CRMDocListView(View):
    # template_name = 'oscar/dashboard/crm/crm_receipts_list.html'
    # table_class = CRMReceiptTable
    # context_table_name = "receipts"
    # paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    
    template_name = 'oscar/dashboard/crm/test_list.html'
    context_object_name = "test"
    
    def get_context_data(self):
        try:
            res = EvatorCloud().get_docs()
        except Exception as e:
            res = []
            logger.error("Error CRMDocListView - %s" % str(e))

        return res
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(request, self.template_name, {self.context_object_name: context})
    
