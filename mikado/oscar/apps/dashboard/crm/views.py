from django.contrib import messages
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from oscar.apps.crm.client import EvatorCloud
from oscar.apps.customer.serializers import StaffsSerializer
from oscar.apps.dashboard.crm.mixins import CRMTablesMixin
from oscar.apps.partner.serializers import PartnersSerializer, TerminalsSerializer
from oscar.core.loading import get_classes, get_model

from django.contrib import messages
from django.shortcuts import redirect
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
        
        data_json = EvatorCloud().get_partners() 
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
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request,
                (f"Ошибка при сериализации данных {serializer.errors}"),
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        msg, success = EvatorCloud().create_or_update_partners(data_items, is_filtered)
        if success:
            messages.success(
                self.request,
                msg,
            )
        else: 
            messages.error(
                self.request,
                msg,
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
        data_json = EvatorCloud().get_terminals() 
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
                    data_item['partners'] = model_instance.partners.all()
                    # Проверка совпадения полей
                    partner_matches = partner_id in model_instance.partners.values_list('evotor_id', flat=True)
                    data_item['is_valid'] = model_instance.name == name and partner_matches
                else:
                    # Партнер не существует
                    data_item['is_created'] = False
                    data_item['is_valid'] = False

            self.queryset = sorted(data_items, key=lambda x: (x['is_created'], x['is_valid']))
            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request,
                (f"Ошибка при сериализации данных {serializer.errors}"),
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        msg, success = EvatorCloud().create_or_update_terminals(data_items, is_filtered)
        if success:
            messages.success(
                self.request,
                msg,
            )
        else: 
            messages.error(
                self.request,
                msg,
            )
        return redirect(self.url_redirect)
    

class CRMStaffListView(CRMTablesMixin):
    template_name = 'oscar/dashboard/crm/staffs/staff_list.html'
    model = Staff
    serializer = StaffsSerializer
    context_table_name = "tables"
    table_prefix = "staff_{}-"
    table_evotor = CRMStaffEvotorTable
    table_site = CRMStaffSiteTable
    url_redirect = reverse_lazy("dashboard:crm-staffs")

    def get_queryset(self):     
        data_json = EvatorCloud().get_staffs() 
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            deserialized_data = serializer.validated_data
            data_items = deserialized_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['evotor_id']

                first_name = data_item.get('first_name', '')
                last_name = data_item.get('last_name', '')
                middle_name = data_item.get('middle_name', '')
                stores_ids = data_item.get('stores', None)
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()
                
                if model_instance:
                    data_item['is_created'] = True
                    data_item['partners'] = model_instance.user.partners.all() if model_instance.user else []
                    partner_evotor_ids = set(model_instance.user.partners.values_list('evotor_id', flat=True)) if model_instance.user else set()
                    partner_matches = bool(partner_evotor_ids.intersection(stores_ids))
                    data_item['is_valid'] = (
                        model_instance.first_name == first_name
                        and model_instance.last_name == last_name
                        and model_instance.middle_name == middle_name
                        and partner_matches
                    )
                else:
                    data_item.update({
                        'partners': stores_ids,
                        'is_created': False,
                        'is_valid': False
                    })

            self.queryset = sorted(data_items, key=lambda x: (x['is_created'], x['is_valid']))
            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request,
                (f"Ошибка при сериализации данных {serializer.errors}"),
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        msg, success = EvatorCloud().create_or_update_staffs(data_items, is_filtered)
        if success:
            messages.success(
                self.request,
                msg,
            )
        else: 
            messages.error(
                self.request,
                msg,
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
    
