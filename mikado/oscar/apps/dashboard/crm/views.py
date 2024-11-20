from django.contrib import messages
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from oscar.apps.catalogue.serializers import ProductsGroupSerializer, ProductsSerializer
from oscar.apps.crm.client import EvatorCloud
from oscar.apps.customer.serializers import StaffsSerializer
from oscar.apps.dashboard.crm.mixins import CRMTablesMixin
from oscar.apps.partner.serializers import PartnersSerializer, TerminalsSerializer
from oscar.core.loading import get_class, get_classes, get_model

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.base import View
from datetime import datetime

import logging

logger = logging.getLogger("oscar.dashboard")

Partner = get_model("partner", "Partner")
Staff = get_model("user", "Staff")
Terminal = get_model("partner", "Terminal")
Order = get_model("order", "Order")
Line = get_model("order", "Line")
Product = get_model('catalogue', 'Product')
Category = get_model("catalogue", "Category")

CRMPartnerForm = get_class("dashboard.crm.forms", "CRMPartnerForm")

(
    CRMPartnerEvotorTable,
    CRMPartnerSiteTable,
    CRMTerminalEvotorTable,
    CRMTerminalSiteTable,
    CRMStaffEvotorTable,
    CRMStaffSiteTable,
    CRMProductEvotorTable,
    CRMProductSiteTable,
    CRMGroupEvotorTable,
    CRMGroupSiteTable,
) = get_classes(
    "dashboard.crm.tables",
    (
        "CRMPartnerEvotorTable",
        "CRMPartnerSiteTable",
        "CRMTerminalEvotorTable",
        "CRMTerminalSiteTable",
        "CRMStaffEvotorTable",
        "CRMStaffSiteTable",
        "CRMProductEvotorTable",
        "CRMProductSiteTable",
        "CRMGroupEvotorTable",
        "CRMGroupSiteTable",
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

        error = data_json.get('error')
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(
                self.request,
                error,
            )
            return self.queryset
        
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['id']
                data_item['updated_at'] = datetime.strptime(data_item['updated_at'], '%Y-%m-%dT%H:%M:%S.%f%z') 
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

        error = data_json.get('error')
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(
                self.request,
                error,
            )
            return self.queryset
        
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['id']
                data_item['updated_at'] = datetime.strptime(data_item['updated_at'], '%Y-%m-%dT%H:%M:%S.%f%z') 
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
                    data_item['partners'] = [partner_id]
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
        
        error = data_json.get('error')
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(
                self.request,
                error,
            )
            return self.queryset
        
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['id']
                data_item['updated_at'] = datetime.strptime(data_item['updated_at'], '%Y-%m-%dT%H:%M:%S.%f%z') 
                first_name = data_item.get('name', None)
                last_name = data_item.get('last_name', None)
                middle_name = data_item.get('patronymic_name', None)
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
   

class CRMGroupsListView(CRMTablesMixin):
    template_name = 'oscar/dashboard/crm/groups/group_list.html'
    model = Category
    form_class = CRMPartnerForm
    serializer = ProductsGroupSerializer
    context_table_name = "tables"
    table_prefix = "group_{}-"
    table_evotor = CRMGroupEvotorTable
    table_site = CRMGroupSiteTable
    url_redirect = reverse_lazy("dashboard:crm-groups")

    def get_queryset(self):     

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Неверные данные формы",
            )
            return []

        data = self.form.cleaned_data
        partner_evotor_id = data.get("partner") or self.form.fields.get("partner").initial

        if not partner_evotor_id:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID точки продаж. Обновите список точек продаж",
            )
            return []
        
        data_json = EvatorCloud().get_groups(partner_evotor_id) 
                
        error = data_json.get('error')
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(
                self.request,
                error,
            )
            return self.queryset
        
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['id']
                data_item['updated_at'] = datetime.strptime(data_item['updated_at'], '%Y-%m-%dT%H:%M:%S.%f%z') 
                # first_name = data_item.get('name', '')
                # last_name = data_item.get('last_name', '')
                # middle_name = data_item.get('patronymic_name', '')
                # stores_ids = data_item.get('stores', None)
                # try:
                #     store_id = data_item['store_id']
                #     data_item['partner'] = Partner.objects.get(evotor_id=store_id)
                # except Exception:
                #     pass

                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()
                
                if model_instance:
                    data_item['is_created'] = True
                    
                    # partner_evotor_ids = set(model_instance.user.partners.values_list('evotor_id', flat=True)) if model_instance.user else set()
                    # partner_matches = bool(partner_evotor_ids.intersection(stores_ids))
                    # data_item['is_valid'] = (
                    #     model_instance.first_name == first_name
                    #     and model_instance.last_name == last_name
                    #     and model_instance.middle_name == middle_name
                    #     and partner_matches
                    # )
                else:
                    data_item.update({
                        # 'partners': stores_ids,
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
        msg, success = EvatorCloud().create_or_update_products(data_items, is_filtered)
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
    

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        return ctx


class CRMProductListView(CRMTablesMixin):
    template_name = 'oscar/dashboard/crm/products/product_list.html'
    model = Product
    form_class = CRMPartnerForm
    serializer = ProductsSerializer
    context_table_name = "tables"
    table_prefix = "product_{}-"
    table_evotor = CRMProductEvotorTable
    table_site = CRMProductSiteTable
    url_redirect = reverse_lazy("dashboard:crm-products")

    def get_queryset(self):     

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Неверные данные формы",
            )
            return []

        data = self.form.cleaned_data
        partner_evotor_id = data.get("partner") or self.form.fields.get("partner").initial

        if not partner_evotor_id:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID точки продаж. Обновите список точек продаж",
            )
            return []
        
        data_json = EvatorCloud().get_products(partner_evotor_id) 

        error = data_json.get('error')
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(
                self.request,
                error,
            )
            return self.queryset
        
        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data['items']
            
            for data_item in data_items:
                evotor_id = data_item['id']
                data_item['updated_at'] = datetime.strptime(data_item['updated_at'], '%Y-%m-%dT%H:%M:%S.%f%z') 
                # first_name = data_item.get('name', '')
                try:
                    store_id = data_item['store_id']
                    data_item['partner'] = Partner.objects.get(evotor_id=store_id)
                except Partner.DoesNotExist:
                    data_item['partner'] = None
                    
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()
                
                if model_instance:
                    data_item['is_created'] = True
                    data_item['is_valid'] = True
                    
                    # partner_evotor_ids = set(model_instance.user.partners.values_list('evotor_id', flat=True)) if model_instance.user else set()
                    # partner_matches = bool(partner_evotor_ids.intersection(stores_ids))
                    # data_item['is_valid'] = (
                    #     model_instance.first_name == first_name
                    #     and model_instance.last_name == last_name
                    #     and model_instance.middle_name == middle_name
                    #     and partner_matches
                    # )
                else:
                    data_item.update({
                        # 'partners': stores_ids,
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
        msg, success = EvatorCloud().create_or_update_products(data_items, is_filtered)
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
        return self.redirect_with_get_params(self.url_redirect, self.request)
    

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        return ctx

 







class CRMDocsListView(View):
    pass

class CRMAcceptListView(View):
    pass

class CRMRevaluationListView(View):
    pass

class CRMWriteOffListView(View):
    pass

class CRMInventoryListView(View):
    pass

class CRMSessionListView(View):
    pass

class CRMCashListView(View):
    pass

class CRMReportListView(View):
    pass



class CRMEventListView(View):
    pass

