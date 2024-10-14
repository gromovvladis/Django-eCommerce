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
from django_tables2 import SingleTableView

from oscar.apps.crm.client import EvatorCloud
from oscar.core.loading import get_class, get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs


import logging
logger = logging.getLogger("oscar.dashboard")

Partner = get_model("partner", "Partner")
Order = get_model("order", "Order")
Line = get_model("order", "Line")


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



class CRMPartnerListView(View):
    # template_name = 'oscar/dashboard/crm/crm_partners_list.html'
    # table_class = CRMPartnerTable
    # context_table_name = "partners"
    # paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    
    template_name = 'oscar/dashboard/crm/test_list.html'
    context_object_name = "test"
    
    def get_context_data(self):
        try:
            res = EvatorCloud().get_partners()
        except Exception as e:
            res = []
            logger.error("Error CRMPartnerListView - %s" % str(e))

        return res
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(request, self.template_name, {self.context_object_name: context})
    

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
    
