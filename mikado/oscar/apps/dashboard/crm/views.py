from django.conf import settings
from django.contrib import messages
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View
from django_tables2 import MultiTableMixin
from django.db.models import Case, When, BooleanField, Q

from django.views.generic import TemplateView
from oscar.apps.crm.client import EvatorCloud
from oscar.apps.customer.serializers import StaffsSerializer
from oscar.apps.dashboard.crm.mixins import CRMTablesMixin
from oscar.apps.partner.serializers import PartnersSerializer, TerminalsSerializer
from oscar.core.loading import get_classes, get_model

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.encoding import smart_str
from django.views.generic.base import View

import logging
logger = logging.getLogger("oscar.dashboard")

Partner = get_model("partner", "Partner")
Staff = get_model("user", "Staff")
Terminal = get_model("partner", "Terminal")
Order = get_model("order", "Order")
Line = get_model("order", "Line")

(
    CRMPartnerEvotorTable,
    CRMPartnerSiteTable,
    CRMTerminalEvotorTable,
    CRMTerminalSiteTable,
    CRMStaffEvotorTable,
    CRMStaffSiteTable,
) = get_classes(
    "dashboard.crm.tables",
    (
        "CRMPartnerEvotorTable",
        "CRMPartnerSiteTable",
        "CRMTerminalEvotorTable",
        "CRMTerminalSiteTable",
        "CRMStaffEvotorTable",
        "CRMStaffSiteTable",
    ),
)

class CRMPartnerListView(CRMTablesMixin):
    template_name = 'oscar/dashboard/crm/partners/partner_list.html'
    model = Partner
    serializer = PartnersSerializer
    context_table_name = "tables"
    table_prefix = "partner_{}-"
    table_evotor = CRMPartnerEvotorTable
    table_site = CRMPartnerSiteTable
    url_redirect = reverse_lazy("dashboard:crm-partners")
    
    def get_queryset(self):
        
        # data_json = EvatorCloud().get_partners() 
        data_json = {
            'items': [
                {
                    'id': '20240713-96AB-40D1-80FA-D455E402869E',
                    'name': 'Мой мага',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T03:44:04.000+0000',
                    'updated_at': '2024-07-13T05:53:32.000+0000'
                },
                {
                    'id': '20240713-774A-4038-8037-E66BF3AA7552',
                    'address': '9 Мая 451',
                    'name': 'Провансик',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                {
                    'id': '20240713-774A-4038-8037-E66BF3AA754',
                    'name': 'Микадо',
                    'user_id': '01-000000010409029',
                    'created_at': '2024-07-13T05:53:31.000+0000',
                    'updated_at': '2024-10-16T11:32:13.000+0000'
                },
                                {
                    'id': '20240713-774A-4038-8037-E66BF3AA7444',
                    'name': 'Микадо 2',
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
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            deserialized_data = serializer.validated_data
            data_items = deserialized_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['evotor_id']
                name = data_item['name']
                address = data_item.get('address')
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()
                
                if model_instance:
                    # Партнер существует: проверяем совпадение полей
                    data_item['is_created'] = True
                    # Проверка совпадения полей
                    address_matches = (address == (model_instance.primary_address.line1 if model_instance.primary_address else None))
                    data_item['is_valid'] = model_instance.name == name and address_matches
                else:
                    # Партнер не существует
                    data_item['is_created'] = False
                    data_item['is_valid'] = False

            self.queryset = sorted(data_items, key=lambda x: (x['is_created'], x['is_valid']))
            return self.queryset
        else:
            return serializer.errors

    def update_models(self, data_items, is_filtered):
        EvatorCloud().create_or_update_partners(data_items, is_filtered)
        messages.success(
            self.request,
            ("Точки продаж были успешно обновлены"),
        )
        return redirect(self.url_redirect)


class CRMTerminalListView(CRMTablesMixin):
    template_name = 'oscar/dashboard/crm/terminals/terminal_list.html'
    model = Terminal
    serializer = TerminalsSerializer
    context_table_name = "tables"
    table_prefix = "terminal_{}-"
    table_evotor = CRMTerminalEvotorTable
    table_site = CRMTerminalSiteTable
    url_redirect = reverse_lazy("dashboard:crm-terminals")

    def get_queryset(self):     
        # data_json = EvatorCloud().get_terminals() 
        data_json = {
            "items": [
                {
                "id": "20170222-D58C-40E0-8051-B53ADFF38860",
                "name": "Моя касса №1",
                "store_id": "20170228-F4F1-401B-80FA-9ECCA8451FFB",
                "timezone_offset": 10800000,
                "imei": "123456789012345",
                "firmware_version": "1.2.3",
                "location": {
                    "lng": 12.34,
                    "lat": 12.34
                },
                "user_id": "00-000000000000000",
                "serial_number":"00307401000000",
                "device_model": "POWER",
                "created_at": "2018-04-17T10:11:49.393+0000",
                "updated_at": "2018-07-16T16:00:10.663+0000"
                }
            ],
            "paging": {
                "next_cursor": "string"
            }
        }
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            deserialized_data = serializer.validated_data
            data_items = deserialized_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['evotor_id']
                name = data_item['name']
                partner_id = data_item.get('store_id')
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()
                
                if model_instance:
                    # Партнер существует: проверяем совпадение полей
                    data_item['is_created'] = True
                    # Проверка совпадения полей
                    partner_matches = (partner_id == (model_instance.partner.evotor_id if model_instance.partner else None))
                    data_item['is_valid'] = model_instance.name == name and partner_matches
                else:
                    # Партнер не существует
                    data_item['is_created'] = False
                    data_item['is_valid'] = False

            self.queryset = sorted(data_items, key=lambda x: (x['is_created'], x['is_valid']))
            return self.queryset
        else:
            return serializer.errors

    def update_models(self, data_items, is_filtered):
        EvatorCloud().create_or_update_terminals(data_items, is_filtered)
        messages.success(
            self.request,
            ("Терминалы были успешно обновлены"),
        )
        return redirect(self.url_redirect)
    

class CRMStaffListView(CRMTablesMixin):
    template_name = 'oscar/dashboard/crm/partners/staff_list.html'
    model = Staff
    serializer = StaffsSerializer
    context_table_name = "tables"
    table_prefix = "staff_{}-"
    table_evotor = CRMStaffEvotorTable
    table_site = CRMStaffSiteTable
    url_redirect = reverse_lazy("dashboard:crm-staffs")

    def get_queryset(self):     
        # data_json = EvatorCloud().get_staffs() 
        data_json = {'items': [{'id': '20240713-4403-40BB-80DA-F84959820434', 'role': 'ADMIN', 'role_id': '20240713-79CF-400A-80A9-EDDBE8702C75', 'name': 'Администратор', 'stores': ['20240713-96AB-40D1-80FA-D455E402869E', '20240713-774A-4038-8037-E66BF3AA7552'], 'user_id': '01-000000010409029', 'created_at': '2024-07-13T03:44:04.000+0000', 'updated_at': '2024-07-13T05:53:32.000+0000'}, {'id': '20240713-9483-4077-809A-8C9EC995166C', 'role': 'CASHIER', 'role_id': '20240713-6E2E-400C-80F0-5E5F0A5A1042', 'name': 'Юлия', 'last_name': 'Кудрявцева', 'stores': ['20240713-96AB-40D1-80FA-D455E402869E', '20240713-774A-4038-8037-E66BF3AA7552'], 'user_id': '01-000000010409029', 'created_at': '2024-07-13T03:44:04.000+0000', 'updated_at': '2024-07-13T05:53:32.000+0000'}, {'id': '20241016-4AD4-408E-80B2-53702AD317D6', 'phone': 79950750095, 'role': 'ADMIN', 'role_id': '20240713-79CF-400A-80A9-EDDBE8702C75', 'name': 'Владислав', 'last_name': 'Громов', 'stores': ['20240713-774A-4038-8037-E66BF3AA7552'], 'user_id': '01-000000010409029', 'created_at': '2024-10-16T11:30:53.000+0000', 'updated_at': '2024-10-16T11:32:13.000+0000'}], 'paging': {}}
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            deserialized_data = serializer.validated_data
            data_items = deserialized_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['evotor_id']
                name = data_item['name']
                partner_id = data_item.get('store_id')
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()
                
                if model_instance:
                    # Партнер существует: проверяем совпадение полей
                    data_item['is_created'] = True
                    # Проверка совпадения полей
                    partner_matches = (partner_id == (model_instance.partner.evotor_id if model_instance.partner else None))
                    data_item['is_valid'] = model_instance.name == name and partner_matches
                else:
                    # Партнер не существует
                    data_item['is_created'] = False
                    data_item['is_valid'] = False

            self.queryset = sorted(data_items, key=lambda x: (x['is_created'], x['is_valid']))
            return self.queryset
        else:
            return serializer.errors

    def update_models(self, data_items, is_filtered):
        EvatorCloud().create_or_update_staffs(data_items, is_filtered)
        messages.success(
            self.request,
            ("Сотрудники были успешно обновлены"),
        )
        return redirect(self.url_redirect)
    




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
    
